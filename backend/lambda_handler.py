"""AWS Lambda handler."""
from mangum import Mangum
from app.main import app

# Create Lambda handler
handler = Mangum(app)
