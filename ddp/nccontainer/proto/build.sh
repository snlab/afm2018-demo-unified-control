#!/bin/bash


~/App/protobuf/bin/protoc --python_out=. tunnel.proto
~/App/protobuf/bin/protoc --python_out=. dataplane.proto
