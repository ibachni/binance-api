import hmac
import hashlib
import requests
import secret
import time

class SendingRequests():

    def __init__(self):
        self.ip_weight = 0
        self.key = secret.key
        self.secret = secret.secret
        self.base_url = "https://api.binance.com"
        self.base_url_alt_1 = "https://api1.binance.com"
        self.base_url_alt_2 = "https://api1.binance.com"
        self.base_url_alt_3 = "https://api1.binance.com"
        self.initialise_requests()
        self.banned = False

    def unpack_parameters(self, dictionary):
        string = ""
        for key in dictionary:
            string += "&{}={}".format(key, dictionary[key])

        return string

    def initialise_requests(self):
        # todo get weight limits
        pass

    def hashing(self, query_string):
        return hmac.new(self.secret.encode("utf-8"), query_string.encode("utf-8"), hashlib.sha256).hexdigest()

    def get_timestamp(self):
        return int(time.time() * 1000)

    def dispatch_request(self, http_method):
        # session allows you to persist certain parameters across requests
        session = requests.Session()
        session.headers.update({"Content-Type": "application/json;charset=utf-8", "X-MBX-APIKEY": self.key})
        return {
            "GET": session.get,
            "DELETE": session.delete,
            "PUT": session.put,
            "POST": session.post}.get(http_method, "GET")

    def send_signed_request(self, http_method, url_path, payload={}):
        query_string = self.unpack_parameters(dictionary=payload)
        current_time = self.get_timestamp()
        if query_string:
            query_string = "{}&timestamp={}".format(query_string, current_time)
        else:
            query_string = "&timestamp={}".format(current_time)
        url = (self.base_url + url_path + "?" + query_string + "&signature=" + self.hashing(query_string))
        # print("{} {}".format(http_method, url))
        params = {"url": url, "params": {}}
        response = self.dispatch_request(http_method)(**params)
        # response_2 is the original response message
        response_2 = response
        print(response_2)
        response = RespObject(response)
        self.ip_weight = response.used_weight
        return response_2, RespObject

    def send_public_request(self, http_method, url_path, payload={}):
        query_string = self.unpack_parameters(dictionary=payload)
        url = self.base_url + url_path
        if query_string:
            url = url + "?" + query_string
        response = self.dispatch_request(http_method)(url=url)
        response_2 = response
        response = RespObject(response)
        self.ip_weight = response.used_weight
        return response_2, RespObject

class RespObject:
    '''
    Used to handle responses from Binance API
    '''
    def __init__(self, response):
        self.status_code = response.status_code
        self.used_weight = response.headers["x-mbx-used-weight"]
        self.elapsed = response.elapsed
        # self.status_code()

    def status_code(self):
        status_code = str(self.status_code)

        #todo create dictionary for lookup

        if status_code[0] == "1":
            level_1_meaning = "(Information): Server acknowledges a request"
        elif status_code[0] == "2":
            level_1_meaning = "(Success): Server completed request as expected"
        elif status_code[0] == "3":
            level_1_meaning = "(Redirection): Clients needs to perform further actions to complete the request"
        elif status_code[0] == "4":
            level_1_meaning = "Malformed requests; the issue is on the sender's side (invalid request)."
        elif status_code[0] == "5":
            level_1_meaning = "internal errors; the issue is on Binance's side. Execution status is unknown " \
                                  "and could have been a success."
        if status_code == "200":
            status_code_meaning = "Everything okay"
        elif status_code == "301":
            status_code_meaning = "The server is redirecting you to a different endpoint"
        elif status_code == "400":
            status_code_meaning = "(Bad request): might be wrong parameters"
        elif status_code == "401":
            status_code_meaning = "(Unauthorized): You are not authenticated: wrong credentials"
        elif status_code == "403":
            status_code_meaning = "(Access Forbidden): WAF Limit (Web Application Firewall) has been violated. (you do" \
                                  "not have the right permissions to see it.)"
        elif status_code == "404":
            status_code_meaning = "(Not Found): The resource you tried to access was not found on the server"
        elif status_code == "409":
            status_code_meaning = "CancelReplace order partially succeeded. (e.g. if the cancellation of the order " \
                                  "fails but the new order placement succeeds.)"
        elif status_code == "418":
            status_code_meaning = "IP has been auto-banned: request send after 429 code."
        elif status_code == "429":
            status_code_meaning = "Rate limit exceeded"
        elif status_code == "500":
            status_code_meaning = "(Internal server error): a generic error occurred on the server"
        elif status_code == "503":
            status_code_meaning = "(Service unavailable): The server is not ready to handle the request"

class Status:
    def __init__(self):
        self.banned = False
        self.ip_weight = 0

class MarketData():

    # todo how to anticipate weight problems e.g., create weight dictionary in order to avoid bans
    # todo consider also getting a speed dictionary: how long does it usually take to answer requests per function
    # todo consider using __init__ to store basic information about MarketData functions, such as expected time,
    # todo expected weight, and params information
    # todo change list of symbols into a list appropriate for parsing as parameter ["hi", "bi"] -> '["hi","bi"]'
    # todo change assignment response = ... return response to return = sendingRequests... (avoid assignment)

    def test_connectivity(self):
        http_method = "GET"
        url_path = "/api/v3/ping"
        response = SendingRequests().send_public_request(http_method=http_method, url_path=url_path)
        return response

    def check_server_time(self):
        http_method = "GET"
        url_path = "/api/v3/time"
        response = SendingRequests().send_public_request(http_method=http_method, url_path=url_path)
        return response

    def get_exchange_information(self, *params):
        #todo response needs to be structured
        '''
        :params: (optional) dictionary structured the following:
            (1) {"symbol": 'BTCUSDT'} (optional)
            (2) {"symbols": '["BNBBTC","ETHBTC"]'} (optional)
            (3) {"permissions": '["SPOT","MARGIN","LEVERAGED"]'} (default is all three) (optional)
        !! no space between individual items in list !!

        If one wants to view al symbols, then one has to search with all permissions explicitly specified
        (["SPOT","MARGIN","LEVERAGED","TRD_GRP_002","TRD_GRP_003","TRD_GRP_004","TRD_GRP_005"])

        :returns: ResponseObject
        '''
        http_method = "GET"
        url_path = "/api/v3/exchangeInfo"
        if params:
            response = SendingRequests().send_public_request(http_method=http_method, url_path=url_path, payload=params[0])
        else:
            response = SendingRequests().send_public_request(http_method=http_method, url_path=url_path)

        return response

    def get_order_book(self, params):
        '''
        :params: dictionary structured the following:
            (1) symbol str (mandatory)
            (2) limit int (optional) (default is 100, max 5000)

        e.g., {"symbol":"BTCUSDT", "limit": 500}

        Weight depends on limit:

        <100: 1
        <500: 5
        <1000: 10
        <5000: 50
        '''
        http_method = "GET"
        url_path = "/api/v3/depth"
        response = SendingRequests().send_public_request(http_method=http_method, url_path=url_path, payload=params)
        return response

    def get_recent_trades_list(self, params):
        '''
        :params: dictionary structured the following:
            (1) symbol str (mandatory)
            (2) limit int (optional) (default is 500, max 1000)
        '''
        http_method = "GET"
        url_path = "/api/v3/trades"
        response = SendingRequests().send_public_request(http_method=http_method, url_path=url_path, payload=params)
        return response

    def get_old_trades_list(self, params):
        '''
        :params: dictionary structured the following:
            (1) symbol str (mandatory)
            (2) limit int (optional) (default is 500, max 1000)
            (3) fromId long (optional) (Tradeid to fetch from. Default gets most recent trades)

        e.g., {"symbol":"BTCUSDT", "limit": 504, "fromId": 10}

        '''
        http_method = "GET"
        url_path = "/api/v3/historicalTrades"
        response = SendingRequests().send_public_request(http_method=http_method, url_path=url_path, payload=params)
        return response

    def get_aggregates_trades_list(self, params):
        #todo find out how to use startTime, endTime parameters (according to docs can only be used together)
        '''
        :params: dictionary structured the following:
            (1) symbol str (mandatory)
            (2) fromId long (optional) (Tradeid to fetch from. Default gets most recent trades)
            (3) startTime long (optional) Timestamp in MS to get aggregate trades from (inclusive)
            (4) endTime long (optional) Timestamp in MS to get aggregate trades until (inclusive)
            (5) limit int (optional) (default is 500, max 1000)

            Either fromId or (startTime and endTime (must be within 1h))
            If neither are sent, most recent aggregate trades will be returned

        e.g., {"symbol":"BTCUSDT", "limit": 504, "fromId": 10}

        '''
        http_method = "GET"
        url_path = "/api/v3/aggTrades"
        response = SendingRequests().send_public_request(http_method=http_method, url_path=url_path, payload=params)
        return response

    def get_klines(self, params):
        #todo find out how to use startTime, endTime parameters (according to docs can only be used together)
        '''
        :params: dictionary structured the following:
            (1) symbol str (mandatory)
            (2) interval enum (mandatory)
            (3) startTime long (optional) Timestamp in MS to get aggregate trades from (inclusive)
            (4) endTime long (optional) Timestamp in MS to get aggregate trades until (inclusive)
            (5) limit int (optional) (default is 500, max 1000)

            If startTime, endTime are not sent, most recent aggregate trades will be returned

        e.g., {"symbol": "BTCUSDT", "interval": "1m", "limit": 100, "startTime": 1646903551336, "endTime": 1646903551336+1500000})

        '''
        http_method = "GET"
        url_path = "/api/v3/klines"
        response = SendingRequests().send_public_request(http_method=http_method, url_path=url_path, payload=params)
        return response

    def get_ui_klines(self, params):
        '''
        same as before, but apparently the return is modified for presentation of candlestick charts

        :params: dictionary structured the following:
            (1) symbol str (mandatory)
            (2) interval enum (mandatory)
            (3) startTime long (optional) Timestamp in MS to get aggregate trades from (inclusive)
            (4) endTime long (optional) Timestamp in MS to get aggregate trades until (inclusive)
            (5) limit int (optional) (default is 500, max 1000)

            If startTime, endTime are not sent, most recent aggregate trades will be returned

        e.g., {"symbol": "BTCUSDT", "interval": "1m", "limit": 100, "startTime": 1646903551336, "endTime": 1646903551336+1500000})

        '''
        http_method = "GET"
        url_path = "/api/v3/uiKlines"
        response = SendingRequests().send_public_request(http_method=http_method, url_path=url_path, payload=params)
        return response

    def get_current_avg_price(self, params):
        '''
        :params: dictionary structured the following:
            (1) symbol str (mandatory)

        e.g., {"symbol": "BTCUSDT")

        '''
        http_method = "GET"
        url_path = "/api/v3/avgPrice"
        response = SendingRequests().send_public_request(http_method=http_method, url_path=url_path, payload=params)
        return response

    def get_daily_price_change_statistics(self, *params):
        '''
        :params: dictionary structured the following:
            (1) symbol str (optional)
                    or
            (2) symbols str (optional)
            (3) type enum (optional) (supported values: FULL or MINI (default: FULL)
                (FULL returns more information, e.g., priceChange, weightedAvgPrice etc.)

            Weight depends on number of symbols. If symbol or symbols parameter is omitted, weight is 40.

        e.g., {"symbol": "BTCUSDT")

        '''
        http_method = "GET"
        url_path = "/api/v3/ticker/24hr"
        if params:
            response = SendingRequests().send_public_request(http_method=http_method, url_path=url_path, payload=params)
        else:
            response = SendingRequests().send_public_request(http_method=http_method, url_path=url_path)
        return response

    def get_symbol_price_ticker(self, *params):
        '''
        Latest price for a symbol or symbols.

        :params: dictionary structured the following:
            (1) symbol str (optional)
                    or
            (2) symbols str (optional)

            Weight depends on number of symbols. If omitted, weight = 2.

        e.g., {"symbol": "BTCUSDT")

        '''
        http_method = "GET"
        url_path = "/api/v3/ticker/price"
        if params:
            response = SendingRequests().send_public_request(http_method=http_method, url_path=url_path, payload=params)
        else:
            response = SendingRequests().send_public_request(http_method=http_method, url_path=url_path)
        return response

    def get_symbol_orderbook_ticker(self, *params):
        '''
        Best price/qty on the order book for a symbol or symbols.

        :params: dictionary structured the following:
            (1) symbol str (optional)
                    or
            (2) symbols str (optional)

            Weight depends on number of symbols. If omitted, weight = 2.

        e.g., {"symbol": "BTCUSDT")

        '''
        http_method = "GET"
        url_path = "/api/v3/ticker/bookTicker"
        if params:
            response = SendingRequests().send_public_request(http_method=http_method, url_path=url_path, payload=params)
        else:
            response = SendingRequests().send_public_request(http_method=http_method, url_path=url_path)
        return response

    def get_rolling_window_price_change_statistics(self, params):
        '''
        Best price/qty on the order book for a symbol or symbols.

        :params: dictionary structured the following:
            (1) symbol str (mandatory)
                    or
            (2) symbols str (mandatory)
            (3) windowSize enum (optional) 1m, 2m,..59m,1h,...,23h,1d,...,7d (default: 1d; units cannot be combined)
            (4) type enum (optional) (FULL or MINI)

            Weight => 2 <= 2*len(symbols) <= 50 (caps at 50 regardless of number of symbols)

        e.g., {"symbol": "BTCUSDT", "windowSize": "1h")

        '''
        http_method = "GET"
        url_path = "/api/v3/ticker"
        return SendingRequests().send_public_request(http_method=http_method, url_path=url_path, payload=params)




class SpotAccountTrade():

    def test_new_order(self, params):
        '''
        Tests new order creation and signature/recvWindow long. Crates and validates a new order but does not send
        it into the matching engine
        :params: dictionary structured the following:
            (1) symbol str (mandatory)
            (2) side enum (mandatory)
            (3) type enum (mandatory)
            (4) timeInForce decimal (mandatory) # todo when is it necessary?
            (5) quantity decimal (optional)
            (6) quoteOrderQty decimal (optional)
            (7) price decimal (optional)
            (8) newClientOrderId str (optional) (a unique id among open orders. Automatically generated if not sent)
            (9) strategyId int (optional)
            (10) strategyType int (optional)
            (11) stopPrice decimal (optional)
            (12) trailingDelta long (optional) (see trailing stop FAQ https://github.com/binance/binance-spot-api-docs/blob/master/faqs/trailing-stop-faq.md)
            (13) icebergQty Decimal (optional)
            (14) newOrderRespType enum (optional)
            (15) recvWindow long (optional) (<60,000)
            (16) timestamp long (mandatory)

            Additional mandatory parameters based on type:
            - LIMIT
            - MARKET
            - STOP_LOSS
            - STOP_LOSS_LIMIT
            - TAKE_PROFIT
            - TAKE_PROFIT_LIMIT
            - LIMIT_MAKER (orders that will be rejected if they would immediately match and trade as a taker)
        '''
        http_method = "POST"
        url_path = "/api/v3/order/test"
        return SendingRequests().send_signed_request(http_method=http_method, url_path=url_path, payload=params)







