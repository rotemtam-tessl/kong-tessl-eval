# Utilities

This document covers Kong's utility types and helper functions for common CLI patterns.

## Utility Flag Types

### ConfigFlag

Uses the configured configuration loader to load configuration from a file specified by a flag.

```go { .api }
// ConfigFlag uses the configured configuration loader to load
// configuration from a file specified by a flag
type ConfigFlag string

// BeforeResolve loads the config file before resolution
func (c ConfigFlag) BeforeResolve(kong *Kong, ctx *Context, trace *Path) error
```

### VersionFlag

A flag type that can be used to display a version number.

```go { .api }
// VersionFlag is a flag type that can be used to display a version number
type VersionFlag bool

// BeforeReset prints the version and exits
func (v VersionFlag) BeforeReset(app *Kong, vars Vars) error
```

### ChangeDirFlag

Changes the current working directory to a path specified by a flag early in the parsing process.

```go { .api }
// ChangeDirFlag changes the current working directory to a path
// specified by a flag early in the parsing process
type ChangeDirFlag string

// Decode changes the directory
func (c ChangeDirFlag) Decode(ctx *DecodeContext) error
```

## Utility Types

### Plugins

Dynamically embedded command-line structures. Each element must be a pointer to a structure.

```go { .api }
// Plugins are dynamically embedded command-line structures.
// Each element must be a pointer to a structure.
type Plugins []any
```

## Utility Functions

### ExpandPath

Helper function to expand a relative or home-relative path to an absolute path.

```go { .api }
// ExpandPath is a helper function to expand a relative or home-relative
// path to an absolute path (e.g., ~/.someconf -> /home/user/.someconf)
func ExpandPath(path string) string
```

### HasInterpolatedVar

Returns true if a variable is interpolated in a string.

```go { .api }
// HasInterpolatedVar returns true if the variable "v" is interpolated in string "s".
// Variables are interpolated using the form ${variable} or ${variable=default}.
func HasInterpolatedVar(s string, v string) bool
```

### Visit

Walks all nodes in the model using the provided visitor function.

```go { .api }
// Visit walks all nodes in the model using the provided visitor function
func Visit(node Visitable, visitor Visitor) error
```

### Visitor Types

```go { .api }
// Visitor can be used to walk all nodes in the model
type Visitor func(node Visitable, next Next) error

// Next should be called by Visitor to proceed with the walk
type Next func(err error) error
```

## Usage Examples

### Using ConfigFlag

```go
package main

import (
    "fmt"
    "github.com/alecthomas/kong"
)

type CLI struct {
    // Config flag that automatically loads configuration
    Config kong.ConfigFlag `type:"path" help:"Load configuration from file."`

    Host string `help:"Server host."`
    Port int    `help:"Server port."`
}

func main() {
    var cli CLI

    parser := kong.Must(&cli,
        // Configure JSON as the configuration loader
        kong.Configuration(kong.JSON),
    )

    ctx, err := parser.Parse(os.Args[1:])
    parser.FatalIfErrorf(err)

    // If --config was provided, configuration is automatically loaded
    fmt.Printf("Host: %s, Port: %d\n", cli.Host, cli.Port)
}
```

### Using VersionFlag

```go
type CLI struct {
    // Version flag that displays version and exits
    Version kong.VersionFlag `help:"Show version and exit."`

    Serve struct {
        Port int `help:"Port to listen on." default:"8080"`
    } `cmd:"" help:"Start the server."`
}

func main() {
    var cli CLI

    parser := kong.Must(&cli,
        kong.Name("myapp"),
        kong.Vars{
            "version": "1.2.3",
        },
    )

    ctx, err := parser.Parse(os.Args[1:])
    parser.FatalIfErrorf(err)

    // If --version was specified, version is printed and program exits
    err = ctx.Run()
    ctx.FatalIfErrorf(err)
}
```

### Using ChangeDirFlag

```go
type CLI struct {
    // Change directory before processing
    Dir kong.ChangeDirFlag `type:"path" help:"Change to directory before executing."`

    Build struct{} `cmd:"" help:"Build the project."`
}

func (b *Build) Run() error {
    // Working directory has already been changed
    cwd, _ := os.Getwd()
    fmt.Printf("Building in: %s\n", cwd)
    return nil
}

func main() {
    var cli CLI
    ctx := kong.Parse(&cli)

    err := ctx.Run()
    ctx.FatalIfErrorf(err)
}
```

### Using ExpandPath

```go
type CLI struct {
    Config string `type:"path" help:"Configuration file."`
}

func main() {
    var cli CLI
    ctx := kong.Parse(&cli)

    // Expand home directory and relative paths
    expandedPath := kong.ExpandPath(cli.Config)
    fmt.Printf("Config path: %s\n", expandedPath)

    // Examples:
    // ~/.config/app.json -> /home/user/.config/app.json
    // ./config.json -> /current/dir/config.json
    // config.json -> /current/dir/config.json
}
```

### Using Plugins

```go
// Plugin structure
type LoggingPlugin struct {
    LogLevel string `help:"Log level." default:"info"`
}

// Another plugin
type MetricsPlugin struct {
    MetricsPort int `help:"Metrics port." default:"9090"`
}

type CLI struct {
    // Dynamically embed plugins
    Plugins kong.Plugins

    Serve struct{} `cmd:"" help:"Start the server."`
}

func main() {
    var cli CLI

    // Create plugin instances
    loggingPlugin := &LoggingPlugin{}
    metricsPlugin := &MetricsPlugin{}

    // Add plugins to CLI
    cli.Plugins = kong.Plugins{loggingPlugin, metricsPlugin}

    parser := kong.Must(&cli)

    ctx, err := parser.Parse(os.Args[1:])
    parser.FatalIfErrorf(err)

    // Plugin flags are now available:
    // --log-level=debug
    // --metrics-port=9000
    fmt.Printf("Log level: %s\n", loggingPlugin.LogLevel)
    fmt.Printf("Metrics port: %d\n", metricsPlugin.MetricsPort)
}
```

### Using Visit to Walk the Model

```go
func main() {
    var cli CLI
    parser := kong.Must(&cli)

    // Walk all nodes in the model
    err := kong.Visit(parser.Model, func(node kong.Visitable, next kong.Next) error {
        switch v := node.(type) {
        case *kong.Application:
            fmt.Printf("Application: %s\n", v.Name)

        case *kong.Node:
            fmt.Printf("Node: %s (depth: %d)\n", v.Name, v.Depth())

        case *kong.Flag:
            fmt.Printf("Flag: --%s", v.Name)
            if v.Short != 0 {
                fmt.Printf(" (-%c)", v.Short)
            }
            fmt.Println()

        case *kong.Value:
            fmt.Printf("Value: %s\n", v.Name)
        }

        // Continue walking
        return next(nil)
    })

    if err != nil {
        panic(err)
    }
}
```

### Advanced Visitor Pattern

```go
func collectAllFlags(app *kong.Application) []*kong.Flag {
    var flags []*kong.Flag

    kong.Visit(app, func(node kong.Visitable, next kong.Next) error {
        if flag, ok := node.(*kong.Flag); ok {
            flags = append(flags, flag)
        }
        return next(nil)
    })

    return flags
}

func findCommand(app *kong.Application, name string) *kong.Node {
    var found *kong.Node

    kong.Visit(app, func(node kong.Visitable, next kong.Next) error {
        if n, ok := node.(*kong.Node); ok {
            if n.Name == name && n.Type == kong.CommandNode {
                found = n
                // Stop walking
                return nil
            }
        }
        return next(nil)
    })

    return found
}

func main() {
    var cli CLI
    parser := kong.Must(&cli)

    // Collect all flags
    flags := collectAllFlags(parser.Model)
    fmt.Printf("Total flags: %d\n", len(flags))

    // Find specific command
    cmd := findCommand(parser.Model, "serve")
    if cmd != nil {
        fmt.Printf("Found command: %s\n", cmd.Name)
    }
}
```

### Custom Visitor for Help Generation

```go
func generateCustomHelp(app *kong.Application) string {
    var help strings.Builder

    help.WriteString(fmt.Sprintf("%s - %s\n\n", app.Name, app.Help))

    kong.Visit(app, func(node kong.Visitable, next kong.Next) error {
        switch v := node.(type) {
        case *kong.Node:
            if v.Type == kong.CommandNode {
                help.WriteString(fmt.Sprintf("Command: %s\n", v.Name))
                help.WriteString(fmt.Sprintf("  %s\n", v.Help))
            }

        case *kong.Flag:
            if !v.Hidden {
                help.WriteString(fmt.Sprintf("  --%s: %s\n", v.Name, v.Help))
            }
        }

        return next(nil)
    })

    return help.String()
}
```

### Visitor with Error Handling

```go
func validateModel(app *kong.Application) error {
    return kong.Visit(app, func(node kong.Visitable, next kong.Next) error {
        if flag, ok := node.(*kong.Flag); ok {
            // Validate flag configuration
            if flag.Required && flag.HasDefault {
                return fmt.Errorf("flag %s cannot be both required and have a default", flag.Name)
            }

            if flag.Enum != "" && flag.Default != "" {
                // Check if default is in enum
                enums := flag.EnumMap()
                if !enums[flag.Default] {
                    return fmt.Errorf("default value %s not in enum for flag %s", flag.Default, flag.Name)
                }
            }
        }

        return next(nil)
    })
}

func main() {
    var cli CLI
    parser := kong.Must(&cli,
        kong.PostBuild(func(k *kong.Kong) error {
            // Validate model after construction
            return validateModel(k.Model)
        }),
    )

    ctx, err := parser.Parse(os.Args[1:])
    parser.FatalIfErrorf(err)
}
```

### Early Stopping in Visitor

```go
func findFirstRequiredFlag(app *kong.Application) *kong.Flag {
    var result *kong.Flag

    kong.Visit(app, func(node kong.Visitable, next kong.Next) error {
        if flag, ok := node.(*kong.Flag); ok {
            if flag.Required {
                result = flag
                // Stop visiting by not calling next
                return nil
            }
        }
        return next(nil)
    })

    return result
}
```

### Combining Utility Types

```go
type CLI struct {
    // Multiple utility flags
    Version kong.VersionFlag    `help:"Show version."`
    Config  kong.ConfigFlag     `type:"path" help:"Config file."`
    Dir     kong.ChangeDirFlag  `type:"path" help:"Working directory."`

    // Regular flags
    Verbose bool `help:"Verbose output."`

    // Commands
    Serve struct {
        Port int `help:"Port to listen on." default:"8080"`
    } `cmd:"" help:"Start the server."`
}

func main() {
    var cli CLI

    parser := kong.Must(&cli,
        kong.Name("myapp"),
        kong.Vars{"version": "1.0.0"},
        kong.Configuration(kong.JSON, "config.json"),
    )

    ctx, err := parser.Parse(os.Args[1:])
    parser.FatalIfErrorf(err)

    // All utility flags work together:
    // --version: shows version and exits
    // --config: loads configuration
    // --dir: changes working directory
    err = ctx.Run()
    ctx.FatalIfErrorf(err)
}
```

### Path Expansion in Custom Types

```go
type PathList []string

func (p *PathList) Decode(ctx *kong.DecodeContext) error {
    var s string
    if err := ctx.Scan.PopValueInto("paths", &s); err != nil {
        return err
    }

    // Split and expand each path
    paths := strings.Split(s, ":")
    for _, path := range paths {
        expanded := kong.ExpandPath(path)
        *p = append(*p, expanded)
    }

    return nil
}

type CLI struct {
    // List of paths that will be expanded
    SearchPaths PathList `help:"Colon-separated search paths."`
}

func main() {
    var cli CLI
    ctx := kong.Parse(&cli)

    // Usage: --search-paths="./local:~/.config:/etc/app"
    // Result: ["/current/local", "/home/user/.config", "/etc/app"]
    for _, path := range cli.SearchPaths {
        fmt.Println(path)
    }
}
```

### Model Introspection with Visit

```go
type ModelStats struct {
    Commands   int
    Flags      int
    Positional int
}

func collectStats(app *kong.Application) ModelStats {
    var stats ModelStats

    kong.Visit(app, func(node kong.Visitable, next kong.Next) error {
        switch v := node.(type) {
        case *kong.Node:
            if v.Type == kong.CommandNode {
                stats.Commands++
            }
            stats.Positional += len(v.Positional)

        case *kong.Flag:
            stats.Flags++
        }

        return next(nil)
    })

    return stats
}

func main() {
    var cli CLI
    parser := kong.Must(&cli)

    stats := collectStats(parser.Model)
    fmt.Printf("Model contains:\n")
    fmt.Printf("  Commands: %d\n", stats.Commands)
    fmt.Printf("  Flags: %d\n", stats.Flags)
    fmt.Printf("  Positional args: %d\n", stats.Positional)
}
```

### Visitor for Model Documentation

```go
func generateMarkdownDocs(app *kong.Application) string {
    var doc strings.Builder

    doc.WriteString(fmt.Sprintf("# %s\n\n", app.Name))
    doc.WriteString(fmt.Sprintf("%s\n\n", app.Help))

    currentCommand := ""

    kong.Visit(app, func(node kong.Visitable, next kong.Next) error {
        switch v := node.(type) {
        case *kong.Node:
            if v.Type == kong.CommandNode {
                currentCommand = v.Name
                doc.WriteString(fmt.Sprintf("## %s\n\n", v.Name))
                doc.WriteString(fmt.Sprintf("%s\n\n", v.Help))

                if len(v.Aliases) > 0 {
                    doc.WriteString(fmt.Sprintf("Aliases: `%s`\n\n", strings.Join(v.Aliases, "`, `")))
                }
            }

        case *kong.Flag:
            if !v.Hidden {
                doc.WriteString(fmt.Sprintf("### --%s\n\n", v.Name))
                doc.WriteString(fmt.Sprintf("%s\n\n", v.Help))

                if v.HasDefault {
                    doc.WriteString(fmt.Sprintf("Default: `%s`\n\n", v.Default))
                }

                if v.Required {
                    doc.WriteString("**Required**\n\n")
                }
            }
        }

        return next(nil)
    })

    return doc.String()
}
```
