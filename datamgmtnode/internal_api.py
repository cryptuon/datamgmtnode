# API
class InternalAPI:
    def __init__(self, node):
        self.node = node

    async def start(self):
        app = aiohttp.web.Application()
        app.router.add_get('/balance/{address}', self.get_balance)
        app.router.add_post('/transfer', self.transfer)
        # Add more routes as needed
        runner = aiohttp.web.AppRunner(app)
        await runner.setup()
        site = aiohttp.web.TCPSite(runner, 'localhost', 8080)
        await site.start()

    async def get_balance(self, request):
        address = request.match_info['address']
        balance = self.node.token_manager.get_balance(address, self.node.get_native_token_address())
        return aiohttp.web.json_response({'balance': balance})

    async def transfer(self, request):
        data = await request.json()
        try:
            success, tx_hash = self.node.payment_processor.process_payment(
                data['from'], data['to'], data['amount'], data['token']
            )
            return aiohttp.web.json_response({'success': success, 'tx_hash': tx_hash})
        except ValueError as e:
            return aiohttp.web.json_response({'error': str(e)}, status=400)