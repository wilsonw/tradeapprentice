import random


EXCHANGE_SPREAD = 5. # mid price difference among exchanges. in percentage
MAX_VOLATILITY = 8. # percentage that next price will jump up or down
BASE_MID_PRICE = 13000.
BASE_SPREAD = 1. # in percentage
DPS = 6

class MockExchange( object ):

    def __init__( self, uid, baseExchange=None ):
        self.rgen = random.SystemRandom( uid )
        self.uid = uid
        self.baseExchange = baseExchange
        self.mid_price = 0.
        self.bid_price = 0.
        self.offer_price = 0.
        self.real_ccy_balance = 0.
        self.crypto_ccy_balance = 0.
        self.tick()

    def tick( self ):
        if self.baseExchange:
            self.mid_price = self._round( self.baseExchange.mid_price * ( 1 - ( EXCHANGE_SPREAD - self.rgen.random() * EXCHANGE_SPREAD * 2 ) / 100. ) )
        else:
            #this is base exchange
            self.mid_price = self.mid_price or BASE_MID_PRICE
            self.mid_price = self._round( self.mid_price * ( 1 - ( MAX_VOLATILITY - self.rgen.random() * MAX_VOLATILITY * 2 ) / 100. ) )
        self.bid_price = self._round( self.mid_price - self.mid_price * ( BASE_SPREAD * self.rgen.random() ) / 100. )
        self.offer_price = self._round( self.mid_price + self.mid_price * ( BASE_SPREAD * self.rgen.random() ) / 100. )
        self.printStatus()

    def realToCrypto( self ):
        return self._round( self.real_ccy_balance / self.offer_price )

    def cryptoToReal( self ):
        return self._round( self.crypto_ccy_balance * self.bid_price )

    def buyWithReal( self, amount ):
        if not self.real_ccy_balance or self.real_ccy_balance < amount:
            raise Exception( 'You have not enough money to buy from Exchange %d' % self.uid )
        self.real_ccy_balance -= amount
        self.crypto_ccy_balance += self._round( amount / self.offer_price )
        print 'Bounght %f coins with cash: %f' % ( self._round( amount / self.offer_price ), amount )

    def buyWithCrypto( self, amount ):
        if not self.real_ccy_balance or self.realToCrypto() < amount:
            raise Exception( 'You have not enough money to buy from Exchange %d' % self.uid )
        self.real_ccy_balance -= self._round( amount * self.offer_price )
        self.crypto_ccy_balance += amount
        print 'Bounght %f coins with cash: %f' % ( amount, self._round( amount * self.offer_price ) )

    def sellWithReal( self, amount ):
        if not self.crypto_ccy_balance or self.cryptoToReal() < amount:
            raise Exception( 'You have not enough coin to sell from Exchange %d' % self.uid )
        self.crypto_ccy_balance -= self._round( amount / self.bid_price )
        self.real_ccy_balance += amount
        print 'Sold %f coins with cash: %f' % ( self._round( amount / self.bid_price ), amount )

    def sellWithCrypto( self, amount ):
        if not self.crypto_ccy_balance or self.crypto_ccy_balance < amount:
            raise Exception( 'You have not enough coin to sell from Exchange %d' % self.uid )
        self.crypto_ccy_balance -= amount
        self.real_ccy_balance += self._round( amount * self.bid_price )
        print 'Sold %f coins with cash: %f' % ( self._round( amount / self.bid_price ), amount )

    def printStatus( self ):
        print 'Exchange %d (Primary: %s): MID: %f, BID: %f, OFFER: %f' % ( self.uid, self.baseExchange is None, self.mid_price, self.bid_price, self.offer_price )
        print 'Cash: %f, Crypto: %f' % ( self.real_ccy_balance, self.crypto_ccy_balance )

    def _round( self, price ):
        return round( price, DPS )


def totalCapital( exchanges ):
    all_real_ccy_balance = 0.
    all_crypto_ccy_balance = 0.
    all_unrealised_balance = 0.
    for ex in exchanges:
        all_real_ccy_balance += ex.real_ccy_balance
        all_crypto_ccy_balance += ex.crypto_ccy_balance
        all_unrealised_balance += ( ex.real_ccy_balance + ex.crypto_ccy_balance * ex.bid_price )
    print 'Total Cash: %f, Total Crypto: %f, Total Unrealised Cash: %f' % (all_real_ccy_balance, all_crypto_ccy_balance, all_unrealised_balance)
    print '=' * 50


def trade( exchanges ):
    # we buy from lowest_offer_price and sell on highest_bid_price
    lowest_offer_price = 0.
    lowest_offer_exchange = None
    highest_bid_price = 0.
    highest_bid_exchange = None
    for ex in exchanges:
        if not lowest_offer_price or ex.offer_price < lowest_offer_price:
            lowest_offer_price = ex.offer_price
            lowest_offer_exchange = ex
        if not highest_bid_price or ex.bid_price > highest_bid_price:
            highest_bid_price = ex.bid_price
            highest_bid_exchange = ex
    if lowest_offer_price and highest_bid_price \
        and lowest_offer_price < highest_bid_price and lowest_offer_exchange != highest_bid_exchange\
        and lowest_offer_exchange.real_ccy_balance and highest_bid_exchange.crypto_ccy_balance:
        # Trade
        if lowest_offer_exchange.real_ccy_balance > 1000.:
            if highest_bid_exchange.cryptoToReal() < lowest_offer_exchange.real_ccy_balance * 0.8: # time to rebalanace
                tradedRealCcyAmount = min( lowest_offer_exchange.real_ccy_balance, highest_bid_exchange.cryptoToReal() )
                lowest_offer_exchange.buyWithReal( tradedRealCcyAmount )
                highest_bid_exchange.sellWithReal( tradedRealCcyAmount )
            else:
                tradedRealCcyAmount = min( lowest_offer_exchange.realToCrypto(), highest_bid_exchange.crypto_ccy_balance )
                lowest_offer_exchange.buyWithCrypto( tradedRealCcyAmount )
                highest_bid_exchange.sellWithCrypto( tradedRealCcyAmount )
            return

    print 'No trade made, skip round'


def main( numOfExchanges=2, numOfRound=1000 ):
    initial_real_ccy_balance = 10000.
    initial_crypto_ccy_balance = round( initial_real_ccy_balance / BASE_MID_PRICE, DPS )

    allExchanges = []
    for i in xrange( numOfExchanges ):
        if i == 0:
            ex = MockExchange( i )
            baseExchange = ex
        else:
            ex = MockExchange( i, baseExchange )
        if i % 2:
            ex.crypto_ccy_balance = initial_crypto_ccy_balance
        else:
            ex.real_ccy_balance = initial_real_ccy_balance
        allExchanges.append( ex )
    totalCapital( allExchanges )

    count = 0
    while( count < numOfRound ):
        for ex in allExchanges:
            ex.tick()
        trade( allExchanges )
        totalCapital( allExchanges )
        count += 1
