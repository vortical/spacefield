### Building and running while developing

Start application by running:
`docker compose up --build`.

It will be running at http://localhost:8000.

### Deploying your application to the cloud

Build image, e.g.: `docker build -t myregistry.com/spacefield .`.

If your cloud uses a different CPU architecture than your development
machine (e.g., you are on a Mac M1 and your cloud provider is amd64),
you'll want to build the image for that platform, e.g.:
`docker build --platform=linux/amd64 -t myregistry.com/spacefield .`.

Then, push it to your registry, e.g. `docker push myregistry.com/spacefield`.
