# Server AWS requirements

## Instalation
[documentation](https://docs.airbyte.com/deploying-airbyte/on-aws-ec2/)

### Install packge dependencies
```
apt install git
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
```
## Execute

cd airbyte
docker-compose up
