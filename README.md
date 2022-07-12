1# Server AWS requirements

## Instalation
[documentation](https://docs.airbyte.com/deploying-airbyte/on-aws-ec2/)

### Install packge dependencies
```
apt install git python python3-pip
```

### Install docker
```
apt intall docker-compose
systemctl start docker
```
or
```
apt install docker-ce
sudo curl -L "https://github.com/docker/compose/releases/download/1.23.2/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
sudo ln -s /usr/local/bin/docker-compose /usr/bin/docker-compose
systemctl start docker
```


### install airbyte
```
git clone https://github.com/airbytehq/airbyte.git
```
### install the scraper
```
cd airbyte/airbyte-integrations/connectors/
git clone https://github.com/Lautarotetamusa/inmuebles24-scraper.git
mv -r inmuebles24-scraper/ source_inmuebles24
cd source_inmuebles24/
```
## Execute
```
sudo pip install -r requirements.txt
sudo docker build . -t airbyte/source-inmuebles24:dev
```
test the scraper
```
sudo docker run --rm -v $(pwd)/secrets:/secrets -v $(pwd)/integration_tests:/integration_tests airbyte/source-inmuebles24:dev read --config /secrets/config.json --catalog /integration_tests/configured_catalog.json
```
## Web
```
sudo docker-compose up
```
go to localhost:8000

## Add the source to the UI
[Setup etl sources video](https://airbyte.com/blog/how-to-build-etl-sources-in-under-30-minutes)

Docker repository name:  airbyte/source-inmuebles24
Docker image tag: dev
