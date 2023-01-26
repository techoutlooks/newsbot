# Local:
#   DOCKER_IMAGE=newsbot:v1
#   CRAWL_DB_URI=mongodb+srv://techu:<password>@cluster0.6we1byk.mongodb.net/scraped_news_db/?retryWrites=true&w=majority
#   docker build --ssh default -t $DOCKER_IMAGE .
#   docker run -v newsbot-data:/newsbot --network host --name newsbot $DOCKER_IMAGE
# GCP
#   gcloud builds submit --tag gcr.io/$PROJECT_ID/$DOCKER_IMAGE .
#   gcloud run deploy newsbot --image gcr.io/$PROJECT_ID/$DOCKER_IMAGE \--region us-central1 --platform managed --allow-unauthenticated -update-env-vars CRAWL_DB_URI=$CRAWL_DB_URI --quiet
#
FROM python:3.9

RUN mkdir -p /newsbot
WORKDIR /newsbot

# Copy files
COPY requirements/prod.txt ./requirements.txt
COPY crawler ./crawler
COPY ezines ./ezines
COPY scrapy.cfg ./
COPY run.py  ./

# Install packages, etc.
RUN python -m pip install pip-tools
RUN python -m piptools sync

# Run crawlers and nlp tasks every 15mn
ENV CRAWL_SCHEDULE 15
CMD ["python", "run.py"]