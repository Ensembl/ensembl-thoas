import asyncio
import asyncio.subprocess


async def launch_subprocess(number):
    await asyncio.create_subprocess_shell(
        f'echo {number}; sleep 5; echo {number} done!'
    )


if __name__ == '__main__':
    for i in range(1, 10):
        asyncio.run(launch_subprocess(i))
