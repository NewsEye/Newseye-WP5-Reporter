# NewsEye WP5  - Reporter

This is a development repo, you are probably in the wrong place

## Deployment
To update the code on the server, run the below commands:
````sh
ssh melkki.cs.helsinki.fi
ssh newseye-wp5.cs.helsinki.fi
sudo su - newseye
cd reporter
git pull origin master
sudo systemctl restart reporter.service
````
