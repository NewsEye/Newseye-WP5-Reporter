# NewsEye WP5  - Reporter

This is a development repo, you are probably in the wrong place

## Dependencies

### FOMA

The morphological realization for English is dependent on the Foma library. On ubuntu/debian, this should be available
from `apt`.

### Python dependencies

The software is being developed using python 3.6, which is the only officially supported version. At the same time,
we see no reason why the Reporter would fail to run on never versions of Python as well. Let us now if you come
across any problems.

Python library dependencies are defined in requirements.txt, and can be installed by running
```bash
 $ pip install -r requirements.txt
```

Again, we've only really tested the software using the specific versions listed in the file.

## Deployment to production

To update the code on the server, run the below commands:
````sh
ssh melkki.cs.helsinki.fi
ssh newseye-wp5.cs.helsinki.fi
sudo su - newseye
cd reporter
git pull origin master
sudo systemctl restart reporter.service
````
