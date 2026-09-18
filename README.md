# pochva-geodata

Минимальные `geoip.dat` и `geosite.dat` для Xray/Happ — собраны из официальных источников v2fly, но содержат только нужные категории (в отличие от полных мировых баз, которые упираются в лимит памяти туннеля на мобильных клиентах, например 50 МБ на iOS).

- `geosite.dat`: `category-ru`, `category-ads-all`, `steam`, `riot` — собрано из [v2fly/domain-list-community](https://github.com/v2fly/domain-list-community) через встроенный `-datprofile` allowlist.
- `geoip.dat`: `ru`, `private` — собрано из [v2fly/geoip](https://github.com/v2fly/geoip) (источник IP-данных — бесплатная DB-IP Country Lite).

Пересобирается автоматически каждый день ([.github/workflows/build.yml](.github/workflows/build.yml)) и публикуется в ветку `release`.

## Ссылки для использования (Happ Geoipurl / Geositeurl)

- `https://raw.githubusercontent.com/MineCube1488/pochva-geodata/release/geoip.dat`
- `https://raw.githubusercontent.com/MineCube1488/pochva-geodata/release/geosite.dat`

## Локальная пересборка

```bash
# geosite.dat
git clone --depth 1 https://github.com/v2fly/domain-list-community.git dlc
cp geosite-profile.json dlc/profile.json
cd dlc && go run ./ -datprofile=./profile.json -outputdir=../output

# geoip.dat
git clone --depth 1 https://github.com/v2fly/geoip.git geoip
cp geoip-config.json geoip/config-pochva.json
cd geoip
curl -L -o dbip.mmdb.gz "https://download.db-ip.com/free/dbip-country-lite-$(date +%Y)-$(date +%m).mmdb.gz"
gzip -d dbip.mmdb.gz && mkdir -p db-ip && mv dbip.mmdb db-ip/dbip-country-lite.mmdb
go run ./ -c ./config-pochva.json
```
