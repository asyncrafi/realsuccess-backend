import environ

# Initialize environ
env = environ.Env()

# Get environment type
DEBUG = env("DEBUG", default="False")

print(f"🐉 DEBUG mode is set to: {DEBUG} 🚸")

if str(DEBUG).lower() in ["false", "0", "no"]:
    from .production import *
else:
    from .development import *
