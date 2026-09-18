# pochva-geodata

Минимальные `geoip.dat` и `geosite.dat` для Xray/Happ — собраны из официальных источников v2fly, но содержат только нужные категории (в отличие от полных мировых баз, которые упираются в лимит памяти туннеля на мобильных клиентах, например 50 МБ на iOS).

- `geosite.dat`: `category-ru`, `category-ads-all`, `steam`, `riot` — собрано из [v2fly/domain-list-community](https://github.com/v2fly/domain-list-community) через встроенный `-datprofile` allowlist.
- `geoip.dat`: `ru`, `private` — собрано из [v2fly/geoip](https://github.com/v2fly/geoip) (источник IP-данных — бесплатная DB-IP Country Lite).

Пересобирается автоматически каждый день ([.github/workflows/build.yml](.github/workflows/build.yml)) и публикуется в ветку `release`.

## Ссылки для использования (Happ Geoipurl / Geositeurl)

- `https://raw.githubusercontent.com/MineCube1488/pochva-geodata/release/geoip.dat`
- `https://raw.githubusercontent.com/MineCube1488/pochva-geodata/release/geosite.dat`

## happ_routing_profile.json

Плейн-JSON профиль маршрутизации Happ (не deeplink). Задан напрямую в поле **Settings → Subscription Settings → Happ routing rules** панели 3x-ui как HTTPS-ссылка:

```
https://raw.githubusercontent.com/MineCube1488/pochva-geodata/main/happ_routing_profile.json
```

3x-ui сам умеет читать по ссылке plain-JSON профиль роутинга (не только deeplink) и переупаковывает его в `happ://routing/onadd/...` внутри подписки — обновляет кэш каждые 5 минут фоновой задачей (`RemoteRoutingJob`, `@every 5m`) плюс живая ревалидация по ETag с TTL 10 минут. Значит после `git push` с изменениями в этом файле новые правила доедут до всех клиентов **автоматически**, в течение ~5–10 минут — без захода в панель.


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
