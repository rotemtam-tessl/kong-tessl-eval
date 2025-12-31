#!/bin/bash
set -e
sed -i 's/kong.Parse(&cli)/kong.Parse(\&cli, kong.WithHyphenPrefixedParameters(true))/' main.go
