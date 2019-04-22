from __future__ import print_function
import pickle
import re
import os
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

# If modifying these scopes, delete the file token.pickle.
SCOPES = [
    "https://www.googleapis.com/auth/admin.directory.user",
    "https://www.googleapis.com/auth/admin.directory.group",
]

qmailGroups = {}
service = None


def lookupGroup(email):
    """Lookup a group based on the email"""
    print("group email: %s" % email)
    results = None
    try:
        results = service.groups().get(groupKey=email).execute()
    except Exception:
        pass

    if results is not None:
        print("results: %s" % results)
        return True
    else:
        return False


def lookupEmail(email):
    """"Lookup an email based on the email"""
    print("email: %s" % email)
    results = None
    try:
        results = service.users().get(userKey=email).execute()
    except Exception:
        pass

    if results is not None:
        print("results: %s" % results)
        return True
    else:
        return False


def handleEmailRedirect(domain, email):
    "Create a redirect for a provided email and its 'aliases'"
    if not lookupEmail(email):
        print("Direct email not found for: {}".format(email))
        if not lookupGroup(email):
            print("No group email for: {}, creating one".format(email))

            aliases = openAliases(domain, email)
            print("email: {} has aliases: {}".format(email, aliases))

            if aliases:
                objectGroup = {}
                objectGroup["name"] = "qmail redirect for: {}".format(email)
                objectGroup["email"] = email
                resultInsert = (
                    service.groups().insert(body=objectGroup).execute()
                )

                print("insert result: %s" % resultInsert)
                if resultInsert["id"]:
                    for alias in aliases:
                        groupInfo = {
                            "email": alias,
                            "role": "MEMBER",
                            "type": "USER",
                        }
                        resultAdd = (
                            service.members()
                            .insert(
                                groupKey=resultInsert["id"], body=groupInfo
                            )
                            .execute()
                        )
                        print("add result: %s" % resultAdd)


def parse_qmail(domain):
    """Parse qmail files

    they are supposed to be stored in qmail-list under our current
    path

    """
    entries = os.listdir("qmail-list/")
    domainWithoutCom = domain.replace(".com", "")
    search_string = "qmail-{}-(.*)".format(domainWithoutCom)
    for entry in entries:
        m = re.search(search_string, entry)
        # print('entry: %s' % entry)
        if m is not None:
            email = m.group(1) + "@{}".format(domain)
            print("Looking up %s" % email)
            handleEmailRedirect(domain, email)


def main():
    """Out main code which initializes the token"""
    global service
    creds = None
    # The file token.pickle stores the user's access and refresh
    # tokens, and is created automatically when the authorization flow
    # completes for the first time.
    if os.path.exists("token.pickle"):
        with open("token.pickle", "rb") as token:
            creds = pickle.load(token)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                "credentials.json", SCOPES
            )
            creds = flow.run_local_server()
        # Save the credentials for the next run
        with open("token.pickle", "wb") as token:
            pickle.dump(creds, token)

    service = build("admin", "directory_v1", credentials=creds)


def returnEmails():
    """Helper function to return the list of emails present on our server
    - not called

    """
    print("Getting the first 10 users in the domain")
    results = (
        service.users()
        .list(customer="my_customer", maxResults=10, orderBy="email")
        .execute()
    )
    users = results.get("users", [])

    if not users:
        print("No users in the domain.")
    else:
        print("Users:")
        for user in users:
            print(
                u"{0} ({1})".format(
                    user["primaryEmail"], user["name"]["fullName"]
                )
            )


def returnGroups():
    """Helper function to return the list of groups present on our server
    - not called

    """
    # Call the Admin SDK Directory API
    print("Getting the first 10 groups in the domain")
    results = (
        service.groups()
        .list(customer="my_customer", maxResults=10, orderBy="email")
        .execute()
    )
    groups = results.get("groups", [])

    if not groups:
        print("No qgroups in the domain.")
    else:
        print("Groups:")
        for group in groups:
            print("Group email: {}".format(group["email"]))

            results = service.members().list(groupKey=group["id"]).execute()
            # print("results: %s" % results)
            members = results.get("members", [])
            for member in members:
                if member["type"] == "USER":
                    print(" %s" % member["email"])

            print("")


def openAliases(domain, email):
    """Open an alias file and append to it our domain"""
    print("openAliases({}, {})".format(domain, email))
    domainWithoutCom = domain.replace(".com", "")
    emailNoDomain = email.replace("@{}".format(domain), "")
    data = ""
    filename = "qmail-list/qmail-{}-{}".format(domainWithoutCom, emailNoDomain)
    with open(filename) as alias_file:
        data = alias_file.read()
    alias_file.close()

    # print("data: %s" % data)
    relevant_aliases = []
    for line in data.split("\n"):
        if not line.startswith("&"):
            continue

        line = line.replace("&", "")

        line = line.replace("{}.test-google-a.com".format(domain), domain)
        if line == email:
            continue  # Prevent self-loop caused by {domain}.test-google-a.com

        if "@localhost" in line:
            continue  # Skip elements that redirect locally into fortress

        print("line: %s" % line)

        if len(line) > 0:
            relevant_aliases.append(line)

    if len(relevant_aliases) == 0:
        print("No relevant aliases for: %s (%s)" % (email, data))
        return None

    print("relevant_aliases: %s" % relevant_aliases)
    return relevant_aliases


if __name__ == "__main__":
    main()
    # returnEmails()

    # returnGroups()
    # exit(0)

    # Test code
    # email = 'test@email.com'
    # if not lookupEmail(email):
    # if not lookupGroup(email):
    #     print("email: %s has no Account or Group Email" % email)
    #     aliases = openAliases(email)
    #     if aliases:
    #         objectGroup = {}
    #         objectGroup['name'] = "qmail redirect for: {}".format(email)
    #         objectGroup['email'] = email
    #         objectGroup['aliases'] = aliases
    #         resultInsert = service.groups().insert(body=objectGroup).execute()

    #         print("insert result: %s" % resultInsert)
    #         if resultInsert['id']:
    #             for alias in aliases:
    #                 groupInfo = {"email": alias, "role": "MEMBER", "type": "USER"}
    #                 resultAdd = service.members().insert(groupKey=resultInsert['id'], body=groupInfo).execute()
    #                 print("add result: %s" % resultAdd)

    parse_qmail("email.com")
