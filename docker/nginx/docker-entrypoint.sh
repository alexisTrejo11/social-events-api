#!/bin/sh
set -e

# Substitute only DOMAIN_NAME variable in the template
envsubst '${DOMAIN_NAME}' < /etc/nginx/templates/app.conf.template > /etc/nginx/conf.d/app.conf

# Start nginx and auto-reload every 6 hours (for cert renewal)
while :; do 
    sleep 6h & 
    wait ${!}
    nginx -s reload
done & 

nginx -g 'daemon off;'
