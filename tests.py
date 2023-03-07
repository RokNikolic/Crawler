import asyncio


async def print1(string: str):
    print(string)
    await asyncio.sleep(0.5)
    print("Done")


async def main():
    todo = ['get 1', 'get 2', 'get 3']

    tasks = [asyncio.create_task(print1(item)) for item in todo]

    done, pending = await asyncio.wait(tasks)


if __name__ == '__main__':
    asyncio.run(main())
