from fasthtml.common import *
from monsterui.all import *
from dotenv import load_dotenv
load_dotenv()
from newsfeed.storage.database import get_session
from newsfeed.web.routes.auth import ar as auth_routes
from newsfeed.web.routes.feed import ar as feed_routes
from starlette.middleware.base import BaseHTTPMiddleware
from newsfeed.web.routes.executive import ar as executive_routes


class DBSessionMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        request.state.db = get_session()
        try:
            response = await call_next(request)
            return response
        finally:
            request.state.db.close()

hdrs = Theme.blue.headers()
app, rt = fast_app(hdrs=hdrs, secret_key='dev-secret')
app.add_middleware(DBSessionMiddleware)

auth_routes.to_app(app)
feed_routes.to_app(app)
executive_routes.to_app(app)

@rt('/')
def get():
    return Redirect('/login')


if __name__ == "__main__":
    serve(appname="newsfeed.web.app")
