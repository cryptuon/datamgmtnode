class ExternalAPI:
    def __init__(self, node):
        self.node = node

    async def start(self):
        app = aiohttp.web.Application()
        app.router.add_post('/share_data', self.share_data)
        app.router.add_get('/verify_data/{data_hash}', self.verify_data)
        app.router.add_get('/get_compliance_history', self.get_compliance_history)
        runner = aiohttp.web.AppRunner(app)
        await runner.setup()
        site = aiohttp.web.TCPSite(runner, '0.0.0.0', 8081)
        await site.start()

    async def share_data(self, request):
        data = await request.json()
        try:
            tx_hash = self.node.share_data(data['data'], data['recipient'], data.get('payment_token'), data.get('payment_amount'))
            return aiohttp.web.json_response({'success': True, 'tx_hash': tx_hash})
        except ValueError as e:
            return aiohttp.web.json_response({'error': str(e)}, status=400)

    async def verify_data(self, request):
        data_hash = request.match_info['data_hash']
        is_verified = self.node.compliance_manager.verify_compliance('data_share', data_hash)
        return aiohttp.web.json_response({'verified': is_verified})

    async def get_compliance_history(self, request):
        filters = request.query.get('filters', '').split(',') if request.query.get('filters') else None
        history = self.node.compliance_manager.get_compliance_history(filters)
        return aiohttp.web.json_response({'history': history})