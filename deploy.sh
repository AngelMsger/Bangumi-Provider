#!/bin/bash

docker login -u "$DOCKER_USERNAME" -p "$DOCKER_PASSWORD";
docker push angelmsger/bangumi-crawler:${TRAVIS_TAG:-latest}
