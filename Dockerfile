FROM python:3.9

RUN mkdir -p /newsbot
WORKDIR /newsbot

# Copy files
COPY ./crawler/requirements/prod.txt ./requirements.txt
COPY ./crawler ./crawler
COPY ./main.py  ./

# Install packages, etc.
RUN python -m pip install pip-tools
RUN python -m piptools sync


# Crawl spiders and run nlp tasks periodically
CMD ["python", "run.py"]