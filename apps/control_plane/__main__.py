import logging
import os
import sys

from apps.control_plane.app import create_app
import uvicorn
from dotenv import load_dotenv


def main() -> None:
    load_dotenv()
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)],
    )
    host = os.environ.get("CONTROL_PLANE_HOST", "127.0.0.1")
    port = int(os.environ.get("CONTROL_PLANE_PORT", "17890"))
    logging.info("Starting control plane on %s:%d", host, port)
    uvicorn.run(create_app(), host=host, port=port)


if __name__ == "__main__":
    main()
