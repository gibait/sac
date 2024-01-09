PROJECT_ID=$1
DATABASE_ID=$2

gcloud functions deploy aggiungi_bolletta \
--runtime python39 \
--trigger-event="providers/cloud.firestore/eventTypes/document.write" \
--trigger-resource="projects/$PROJECT_ID/databases/$DATABASE_ID/documents/letture/{lettura}" \
--docker-registry=artifact-registry