# main entrypoint

import argparse
import uvicorn

from .server import main

if __name__ == '__main__':
    # parse args
    parser = argparse.ArgumentParser()
    parser.add_argument('--provider', type=str, default='anthropic')
    parser.add_argument('--native', action='store_true')
    parser.add_argument('--model', type=str, default=None)
    parser.add_argument('--prefill', default=True, action=argparse.BooleanOptionalAction)
    parser.add_argument('--max-tokens', type=int, default=8192)
    parser.add_argument('--cache-dir', type=str, default='cache')
    parser.add_argument('--host', type=str, default='127.0.0.1')
    parser.add_argument('--port', type=int, default=5000)
    args = parser.parse_args()

    # run server
    app = main(
        provider=args.provider, native=args.native, model=args.model, prefill=args.prefill,
        max_tokens=args.max_tokens, cache_dir=args.cache_dir
    )

    # run in uvicorn
    uvicorn.run(app, host=args.host, port=args.port)
