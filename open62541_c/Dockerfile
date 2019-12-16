FROM alpine:3.10 as builder
RUN apk add --no-cache cmake gcc git g++ musl-dev mbedtls-dev python py-pip make && rm -rf /var/cache/apk/*
ADD . /open62541

#RUN git clone https://github.com/open62541/open62541
#COPY . /open62541

# Get all the git tags to make sure we detect the correct version with git describe
WORKDIR /open62541
#RUN git clone https://github.com/open62541/open62541
# get project from fork
RUN git clone https://github.com/SebastianDD/open62541
WORKDIR /open62541/open62541
RUN git remote add github-upstream https://github.com/open62541/open62541.git
RUN git fetch -f --tags github-upstream
# https://stackoverflow.com/questions/58690455/how-to-correctly-initialize-git-submodules-in-dockerfile-for-docker-cloud
# Ignore error here. This always fails on Docker Cloud. It's fine there because the submodule is already initialized. See also:
RUN git submodule update --init --recursive || true

WORKDIR /open62541/build
RUN cmake -DBUILD_SHARED_LIBS=ON \
		-DCMAKE_BUILD_TYPE=Debug \
		-DUA_BUILD_EXAMPLES=ON \
		# Hardening needs to be disabled, otherwise the docker build takes too long and travis fails
		-DUA_ENABLE_HARDENING=OFF \
        -DUA_ENABLE_ENCRYPTION=ON \
        -DUA_ENABLE_SUBSCRIPTIONS=ON \
        -DUA_ENABLE_SUBSCRIPTIONS_EVENTS=ON \
		-DUA_NAMESPACE_ZERO=FULL \
         /open62541/open62541
RUN make -j
RUN make install
WORKDIR /open62541

# Generate certificates
RUN apk add --no-cache python-dev linux-headers openssl && rm -rf /var/cache/apk/*
RUN pip install netifaces==0.10.9
RUN mkdir -p /open62541/pki/created
RUN python /open62541/open62541/tools/certs/create_self-signed.py /open62541/pki/created


FROM alpine:3.10

RUN  apk add --no-cache mbedtls libgcc musl && rm -rf /var/cache/apk/*
LABEL multi.type="opcua_server_c" multi.version="0.5"

COPY --from=builder /open62541/open62541     /open62541
COPY --from=builder /open62541/build         /open62541/build
COPY --from=builder /open62541/pki/created   /open62541/pki/created
#COPY UC2_grid_protection/open62541_c/custom_server.c                         /open62541/custom/custom_server.c

EXPOSE 4840
#CMD ["/open62541/build/bin/examples/custom_server_simple" , "/open62541/pki/created/server_cert.der", "/open62541/pki/created/server_key.der", "--enableUnencrypted", "--enableAnonymous"]
#CMD ["/open62541/build/bin/examples/custom_server" , "/open62541/pki/created/server_cert.der", "/open62541/pki/created/server_key.der", "--enableUnencrypted", "--enableAnonymous"]
CMD ["/open62541/build/bin/examples/server_access_control"]


#CMD ["/open62541/build/bin/examples/server_ctt" , "/open62541/pki/created/server_cert.der", "/open62541/pki/created/server_key.der", "--enableUnencrypted", "--enableAnonymous"]
#CMD ["/open62541/custom/custom_server.c" , "/open62541/pki/created/server_cert.der", "/open62541/pki/created/server_key.der", "--enableUnencrypted", "--enableAnonymous"]
