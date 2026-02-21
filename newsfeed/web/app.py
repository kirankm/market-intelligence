from fasthtml.common import *
from monsterui.all import *
from dotenv import load_dotenv
load_dotenv()
from newsfeed.storage.database import get_session
from newsfeed.web.routes.auth import ar as auth_routes
from newsfeed.web.routes.feed import ar as feed_routes


def before(req, session):
    req.state.db = get_session()

def after(req, resp):
    if hasattr(req.state, 'db'):
        req.state.db.close()


hdrs = Theme.blue.headers()
app, rt = fast_app(hdrs=hdrs, secret_key='dev-secret',
                   before=Beforeware(before),
                   after=after)

auth_routes.to_app(app)
feed_routes.to_app(app)

@rt('/')
def get():
    return Redirect('/login')


if __name__ == "__main__":
    serve(appname="newsfeed.web.app")
