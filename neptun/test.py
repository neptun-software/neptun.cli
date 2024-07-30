import asyncio


async def main():
    print("Starting task...")
    data = await perform_long_task()
    print("Task completed.")
    print(f"Data: {data}")


async def perform_long_task():
    await asyncio.sleep(5)
    return "Sample Data"

if __name__ == "__main__":
    asyncio.run(main())

