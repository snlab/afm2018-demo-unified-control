import asyncio

from kytos.core import kytosd
# from kytos.cli.commands.napps.parser import parse

def main():
    loop = asyncio.get_event_loop()
    loop.call_soon(kytosd.async_main)
    try:
        loop.run_forever()
    finally:
        loop.close()


if __name__ == '__main__':
    import sys
    print(sys.path)
    sys.argv.extend(["-f"])
    print(sys.argv)
    main()