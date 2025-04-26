include dataconfig.mk
# defines US_TICKERS, LONDON_TICKERS, FMP_API_KEY, AV_API_KEY

AV_PRICES = $(foreach t,$(US_TICKERS),AV/$t.json) $(foreach t,$(LONDON_TICKERS),AV/$t.json)
FMP_US_PRICES = $(foreach t,$(US_TICKERS),FMP/$t.json)
FMP_LON_PRICES =  $(foreach t,$(LONDON_TICKERS),FMP/$t.json)
FMP_PRICES = $(FMP_US_PRICES) # $(FMP_LON_PRICES)
# FMP free plan only covers US stocks
AV_SPLITS = $(foreach t,$(US_TICKERS),AV/Splits/$t.json) $(foreach t,$(LONDON_TICKERS),AV/Splits/$t.json)

.PHONY: all cleanfail

all: $(AV_PRICES) $(FMP_PRICES) $(AV_SPLITS)

cleanfail:
	find . -size 0c -delete

$(AV_PRICES): AV/%.json:
	wget "https://www.alphavantage.co/query?function=TIME_SERIES_MONTHLY_ADJUSTED&symbol=$*&apikey=$(AV_API_KEY)" -O "$@"

$(FMP_US_PRICES): FMP/%.json:
	wget "https://financialmodelingprep.com/api/v3/historical-price-full/$*?apikey=$(FMP_API_KEY)" -O "$@"

$(FMP_LON_PRICES): FMP/%.json:
	wget "https://financialmodelingprep.com/api/v3/historical-price-full/$*ON?apikey=$(FMP_API_KEY)" -O "$@"

$(AV_SPLITS): AV/Splits/%.json:
	wget "https://www.alphavantage.co/query?function=SPLITS&symbol=$*&apikey=$(AV_API_KEY)" -O "$@"

ACWI.json: ACWI.json
	curl "https://www.msci.com/indexes/api/index/performance?indexCode=892400&indexCode=664204&indexCode=990100&indexCode=891800&currency=USD&variant=NETR&frequency=daily&baseValue100=false&startDate=1998-12-31&endDate=`date +%Y-%m-%d`" \
  -H 'Accept: */*' \
  -H 'Accept-Language: en-US,en;q=0.6' \
  -H 'Connection: keep-alive' \
  -H 'Sec-Fetch-Dest: empty' \
  -H 'Sec-Fetch-Mode: cors' \
  -H 'Sec-Fetch-Site: same-origin' \
  -H 'Sec-GPC: 1' \
  -H 'User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36' \
  -H 'sec-ch-ua-mobile: ?0' --output ACWI.json

SPX.json: SPX.json
	curl 'https://www.spglobal.com/spdji/en/util/redesign/index-data/get-performance-data-for-datawidget-redesign.dot?indexId=340&getchildindex=true&returntype=N-&currencycode=USD&currencyChangeFlag=false&language_id=1&_=1745681079167' \
  -H 'accept: application/json, text/javascript, */*; q=0.01' \
  -H 'accept-language: en-US,en;q=0.7' \
  -H 'priority: u=1, i' \
  -H 'referer: https://www.spglobal.com/spdji/en/indices/equity/sp-500/?currency=USD&returntype=N-' \
  -H 'sec-ch-ua-mobile: ?0' \
  -H 'sec-fetch-dest: empty' \
  -H 'sec-fetch-mode: cors' \
  -H 'sec-fetch-site: same-origin' \
  -H 'sec-gpc: 1' \
  -H 'user-agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36' \
  -H 'x-requested-with: XMLHttpRequest' --output SPX.json
