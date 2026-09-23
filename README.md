# pochva-geodata

Минимальные `geoip.dat` и `geosite.dat` для Xray/Happ — собраны из официальных источников v2fly, но содержат только нужные категории (в отличие от полных мировых баз, которые упираются в лимит памяти туннеля на мобильных клиентах, например 50 МБ на iOS).

- `geosite.dat`: `category-ru`, `category-ads-all`, `steam`, `riot` — собрано из [v2fly/domain-list-community](https://github.com/v2fly/domain-list-community) через встроенный `-datprofile` allowlist.
- `geoip.dat`: `ru`, `private` — собрано из [v2fly/geoip](https://github.com/v2fly/geoip) (источник IP-данных — бесплатная DB-IP Country Lite), плюс `steam-ip` и `riot-ip` — анонсируемые префиксы AS32590 и AS6507 из RIPE.

Пересобирается автоматически каждый день ([.github/workflows/build.yml](.github/workflows/build.yml)) и публикуется в ветку `release`.

## Ссылки для использования (Happ Geoipurl / Geositeurl)

- `https://raw.githubusercontent.com/MineCube1488/pochva-geodata/release/geoip.dat`
- `https://raw.githubusercontent.com/MineCube1488/pochva-geodata/release/geosite.dat`

## happ_routing_profile.json

Плейн-JSON профиль маршрутизации Happ (не deeplink). Правится здесь, в `main`, а панель читает **проверенную копию из ветки `release`**. Ссылка в поле **Settings → Subscription Settings → Happ routing rules** панели 3x-ui:

```
https://raw.githubusercontent.com/MineCube1488/pochva-geodata/release/happ_routing_profile.json
```

3x-ui сам умеет читать по ссылке plain-JSON профиль роутинга (не только deeplink) и переупаковывает его в `happ://routing/onadd/...` внутри подписки — обновляет кэш каждые 5 минут фоновой задачей (`RemoteRoutingJob`, `@every 5m`) плюс живая ревалидация по ETag с TTL 10 минут.

### Как профиль попадает к клиентам

После `git push` с изменениями в профиле запускается [publish-profile.yml](.github/workflows/publish-profile.yml):

1. **Проверка категорий.** Каждая `geosite:…` / `geoip:…` из профиля должна уже быть в опубликованных `geosite.dat` / `geoip.dat`. Если какой-то нет — workflow падает (красный крестик + письмо от GitHub), в `release` ничего не уходит, клиенты продолжают получать последний рабочий профиль. Без этой проверки Xray на клиенте не запускается: `failed to check code STEAM from geosite.dat`, в Happ — «Ошибка запуска ядра: EOF».
2. **`LastUpdated` ставится автоматически** при каждом изменении правил. В `main` его руками не трогать. Happ перекачивает geo-файлы, только когда `LastUpdated` вырос.
3. Профиль с `LastUpdated` публикуется в `release` → через ~5–10 минут доезжает до клиентов.

Ежедневная сборка ([build.yml](.github/workflows/build.yml)) тоже сверяет профиль со свежими `.dat` и не публикует их, если из upstream пропала нужная категория.

### Добавление новой категории

Happ перекачивает geo-файлы **не чаще раза в неделю**, даже если `LastUpdated` вырос. Поэтому в два шага:

1. Добавить категорию в `geosite-profile.json` / `geoip-config.json`, дождаться сборки (или запустить её вручную).
2. Примерно через неделю добавить её в `happ_routing_profile.json`. Раньше — проверка пропустит (категория в `.dat` уже есть), но у клиентов, скачавших файлы в последние дни, ядро не запустится.


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
