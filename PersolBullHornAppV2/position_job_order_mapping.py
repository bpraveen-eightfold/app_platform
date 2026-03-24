ef_to_bh_position = {

  "atsEntityId": "id",
  "title": "title",
  "description": "description",
  "company": "clientCorporation.name",
  "status": "status",
  "open": "isOpen",
  "businessUnit": "correlatedCustomText10",
  "lastUpdated": "dateLastModified",
  "createdAt": "dateAdded",
  # "lastUpdated": "dateLastModified",
  "function": "publishedCategory",
  "companyDescription": "clientCorporation.name",
  "evergreen": "customText13",
}

bh_to_ef_position = {
  "id": "atsJobId",
  "description": "jobDescription",
  "title": "name", #"title",
  "dateAdded": "createdAt",
  "status": "status",
  "correlatedCustomText10": "businessUnit",
  "customText13": "evergreen",
  "publishedCategory": "function",
  "dateLastModified": "lastUpdated",
  "isOpen": "isOpen"

}