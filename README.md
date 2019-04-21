# qmail-conversion-google-group-api
Convert Qmail redirects (qmail files) to Google Groups via API

# Enable Directory API
Go to:
 https://developers.google.com/admin-sdk/directory/v1/quickstart/python

Click on the "Enable The Directory API"

Then ask the interface to provide a `credentials.json` file

# Requirements
1. ```apt-get install python3 python3-pip```

2. ```pip3 install --upgrade google-api-python-client google-auth-httplib2 google-auth-oauthlib```

3. API documentation can be found here: ```https://developers.google.com/resources/api-libraries/documentation/admin/directory_v1/python/latest/admin_directory_v1.groups.html```

4. QMail files are usually hidden - so lets bulk rename them to non-hidden files to make our lives easier (not a hard requirement, modify source file if you expect the '.' to be there): ```rename -v 's/\.qmail/qmail/' .qmail*```

