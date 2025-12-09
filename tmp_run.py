import asyncio
from app.services.horizon_service import HorizonService

async def main():
    svc = HorizonService()
    try:
        result = await svc.process_dynamic_request('help')
        print('OK:', result)
    except Exception as e:
        import traceback
        traceback.print_exc()

asyncio.run(main())
