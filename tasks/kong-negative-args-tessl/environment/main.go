package main

import (
	"fmt"

	"github.com/alecthomas/kong"
)

type CLI struct {
	Add AddCmd `cmd:"" help:"Add two integers and print their sum"`
}

type AddCmd struct {
	A int `help:"First integer" required:""`
	B int `help:"Second integer" required:""`
}

func (a *AddCmd) Run() error {
	sum := a.A + a.B
	fmt.Println(sum)
	return nil
}

func main() {
	var cli CLI
	ctx := kong.Parse(&cli)
	err := ctx.Run()
	ctx.FatalIfErrorf(err)
}

