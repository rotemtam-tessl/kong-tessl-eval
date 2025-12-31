# Resolvers

This document covers Kong's resolver system, which loads flag values from external sources like configuration files, environment variables, or custom sources.

## Resolver Interface

```go { .api }
// Resolver resolves a Flag value from an external source
type Resolver interface {
    // Validate validates configuration against Application
    Validate(app *Application) error

    // Resolve resolves the value for a Flag
    Resolve(context *Context, parent *Path, flag *Flag) (any, error)
}

// ResolverFunc is a convenience type for non-validating Resolvers.
// It implements the Resolver interface with a no-op Validate method.
type ResolverFunc func(context *Context, parent *Path, flag *Flag) (any, error)

// Resolve calls the underlying function
func (r ResolverFunc) Resolve(context *Context, parent *Path, flag *Flag) (any, error)

// Validate is a no-op implementation that always returns nil
func (r ResolverFunc) Validate(app *Application) error
```

## Built-in Resolvers

### JSON Resolver

```go { .api }
// JSON returns a Resolver that retrieves values from a JSON source.
// Flag names are used as JSON keys indirectly, by trying snake_case
// and camelCase variants.
func JSON(r io.Reader) (Resolver, error)
```

## Usage Examples

### Using JSON Resolver

```go
package main

import (
    "os"
    "github.com/alecthomas/kong"
)

type Config struct {
    Host string `help:"Server host."`
    Port int    `help:"Server port."`
    Debug bool  `help:"Enable debug mode."`
}

type CLI struct {
    Config Config
}

func main() {
    var cli CLI

    // config.json:
    // {
    //   "host": "localhost",
    //   "port": 8080,
    //   "debug": false
    // }

    file, err := os.Open("config.json")
    if err != nil {
        panic(err)
    }
    defer file.Close()

    resolver, err := kong.JSON(file)
    if err != nil {
        panic(err)
    }

    parser := kong.Must(&cli,
        kong.Resolvers(resolver),
    )

    ctx, err := parser.Parse(os.Args[1:])
    parser.FatalIfErrorf(err)

    // Values from config.json will be used as defaults
    // Command-line flags override config values
}
```

### JSON Resolver with Configuration Option

```go
type CLI struct {
    ConfigFile string `type:"path" help:"Configuration file."`

    Host string `help:"Server host."`
    Port int    `help:"Server port."`
}

func main() {
    var cli CLI

    parser := kong.Must(&cli,
        // Automatically load config from these paths if they exist
        kong.Configuration(kong.JSON, "config.json", "~/.myapp.json"),
    )

    ctx, err := parser.Parse(os.Args[1:])
    parser.FatalIfErrorf(err)
}
```

### JSON with Nested Structures

```go
type Database struct {
    Host     string `help:"Database host."`
    Port     int    `help:"Database port."`
    Username string `help:"Database username."`
    Password string `help:"Database password."`
}

type CLI struct {
    Database Database
    Debug    bool `help:"Enable debug mode."`
}

func main() {
    var cli CLI

    // config.json:
    // {
    //   "database": {
    //     "host": "localhost",
    //     "port": 5432,
    //     "username": "admin",
    //     "password": "secret"
    //   },
    //   "debug": true
    // }

    parser := kong.Must(&cli,
        kong.Configuration(kong.JSON, "config.json"),
    )

    ctx, err := parser.Parse(os.Args[1:])
    parser.FatalIfErrorf(err)

    // cli.Database.Host will be "localhost"
    // cli.Database.Port will be 5432
}
```

### Custom Resolver Function

```go
func envVarResolver() kong.ResolverFunc {
    return func(context *kong.Context, parent *kong.Path, flag *kong.Flag) (any, error) {
        // Build environment variable name from flag name
        envName := strings.ToUpper(strings.ReplaceAll(flag.Name, "-", "_"))
        envName = "MYAPP_" + envName

        // Look up environment variable
        if value, ok := os.LookupEnv(envName); ok {
            return value, nil
        }

        // No value found
        return nil, nil
    }
}

func main() {
    var cli CLI

    parser := kong.Must(&cli,
        kong.Resolvers(envVarResolver()),
    )

    ctx, err := parser.Parse(os.Args[1:])
    parser.FatalIfErrorf(err)

    // Flags can now be set via MYAPP_<FLAG_NAME> environment variables
}
```

### Implementing Full Resolver Interface

```go
type YAMLResolver struct {
    values map[string]any
}

func NewYAMLResolver(r io.Reader) (*YAMLResolver, error) {
    var values map[string]any
    decoder := yaml.NewDecoder(r)
    if err := decoder.Decode(&values); err != nil {
        return nil, err
    }

    return &YAMLResolver{values: values}, nil
}

func (y *YAMLResolver) Validate(app *kong.Application) error {
    // Optionally validate that all config keys correspond to actual flags
    return nil
}

func (y *YAMLResolver) Resolve(context *kong.Context, parent *kong.Path, flag *kong.Flag) (any, error) {
    // Try various key formats
    keys := []string{
        flag.Name,
        strings.ReplaceAll(flag.Name, "-", "_"),
        toCamelCase(flag.Name),
    }

    for _, key := range keys {
        if value, ok := y.values[key]; ok {
            return value, nil
        }
    }

    return nil, nil
}

func toCamelCase(s string) string {
    parts := strings.Split(s, "-")
    for i := 1; i < len(parts); i++ {
        parts[i] = strings.Title(parts[i])
    }
    return strings.Join(parts, "")
}

func main() {
    var cli CLI

    file, err := os.Open("config.yaml")
    if err != nil {
        panic(err)
    }
    defer file.Close()

    resolver, err := NewYAMLResolver(file)
    if err != nil {
        panic(err)
    }

    parser := kong.Must(&cli,
        kong.Resolvers(resolver),
    )

    ctx, err := parser.Parse(os.Args[1:])
    parser.FatalIfErrorf(err)
}
```

### Multiple Resolvers

```go
func main() {
    var cli CLI

    // Create multiple resolvers
    jsonFile, _ := os.Open("config.json")
    defer jsonFile.Close()
    jsonResolver, _ := kong.JSON(jsonFile)

    envResolver := envVarResolver()

    parser := kong.Must(&cli,
        // Resolvers are applied in order
        // Later resolvers override earlier ones
        kong.Resolvers(
            jsonResolver,  // First, load from JSON
            envResolver,   // Then, override with env vars
        ),
    )

    ctx, err := parser.Parse(os.Args[1:])
    parser.FatalIfErrorf(err)

    // Resolution order:
    // 1. JSON config file
    // 2. Environment variables
    // 3. Command-line flags (highest priority)
}
```

### Context-Specific Resolver

```go
func main() {
    var cli CLI
    parser := kong.Must(&cli)

    ctx, err := parser.Parse(os.Args[1:])
    if err != nil {
        parser.FatalIfErrorf(err)
    }

    // Add resolver after parsing
    if userConfigExists() {
        file, _ := os.Open(userConfigPath())
        defer file.Close()
        resolver, _ := kong.JSON(file)

        ctx.AddResolver(resolver)
        ctx.Resolve() // Re-resolve with new resolver
    }

    err = ctx.Run()
    ctx.FatalIfErrorf(err)
}

func userConfigExists() bool {
    return false
}

func userConfigPath() string {
    return ""
}
```

### Clearing and Replacing Resolvers

```go
func main() {
    var cli CLI

    parser := kong.Must(&cli,
        // Clear any default resolvers
        kong.ClearResolvers(),

        // Add only custom resolvers
        kong.Resolvers(
            customResolver1(),
            customResolver2(),
        ),
    )

    ctx, err := parser.Parse(os.Args[1:])
    parser.FatalIfErrorf(err)
}

func customResolver1() kong.Resolver {
    return nil
}

func customResolver2() kong.Resolver {
    return nil
}
```

### Resolver with Path Context

```go
func pathAwareResolver() kong.ResolverFunc {
    return func(context *kong.Context, parent *kong.Path, flag *kong.Flag) (any, error) {
        // Use parent path to determine resolution strategy
        if parent != nil && parent.Command != nil {
            commandName := parent.Command.Name

            // Load command-specific config
            configPath := fmt.Sprintf("config/%s.json", commandName)
            if _, err := os.Stat(configPath); err == nil {
                file, _ := os.Open(configPath)
                defer file.Close()

                var config map[string]any
                json.NewDecoder(file).Decode(&config)

                if value, ok := config[flag.Name]; ok {
                    return value, nil
                }
            }
        }

        return nil, nil
    }
}

type CLI struct {
    Serve struct {
        Port int `help:"Port to listen on."`
    } `cmd:""`

    Build struct {
        Output string `help:"Output directory."`
    } `cmd:""`
}

func main() {
    var cli CLI

    parser := kong.Must(&cli,
        kong.Resolvers(pathAwareResolver()),
    )

    // Will load config/serve.json for serve command
    // Will load config/build.json for build command
    ctx, err := parser.Parse(os.Args[1:])
    parser.FatalIfErrorf(err)
}
```

### Resolver with Validation

```go
type ValidatingResolver struct {
    values map[string]any
}

func (v *ValidatingResolver) Validate(app *kong.Application) error {
    // Check that all config keys correspond to actual flags
    validFlags := make(map[string]bool)

    // Collect all flag names
    var collectFlags func(*kong.Node)
    collectFlags = func(node *kong.Node) {
        for _, flag := range node.Flags {
            validFlags[flag.Name] = true
        }
        for _, child := range node.Children {
            collectFlags(child)
        }
    }
    collectFlags(&app.Node)

    // Check for unknown config keys
    for key := range v.values {
        if !validFlags[key] {
            return fmt.Errorf("unknown config key: %s", key)
        }
    }

    return nil
}

func (v *ValidatingResolver) Resolve(context *kong.Context, parent *kong.Path, flag *kong.Flag) (any, error) {
    if value, ok := v.values[flag.Name]; ok {
        return value, nil
    }
    return nil, nil
}
```

### Fallback Resolver Chain

```go
func createResolverChain(paths []string) kong.Resolver {
    return kong.ResolverFunc(func(context *kong.Context, parent *kong.Path, flag *kong.Flag) (any, error) {
        // Try each config file in order
        for _, path := range paths {
            if _, err := os.Stat(path); os.IsNotExist(err) {
                continue
            }

            file, err := os.Open(path)
            if err != nil {
                continue
            }
            defer file.Close()

            resolver, err := kong.JSON(file)
            if err != nil {
                continue
            }

            // Try to resolve from this file
            value, err := resolver.Resolve(context, parent, flag)
            if err != nil || value != nil {
                return value, err
            }
        }

        // No value found in any file
        return nil, nil
    })
}

func main() {
    var cli CLI

    resolver := createResolverChain([]string{
        "./config.json",           // Project config
        "~/.myapp/config.json",   // User config
        "/etc/myapp/config.json", // System config
    })

    parser := kong.Must(&cli,
        kong.Resolvers(resolver),
    )

    ctx, err := parser.Parse(os.Args[1:])
    parser.FatalIfErrorf(err)
}
```

### Type-Aware Resolver

```go
func typeAwareResolver() kong.ResolverFunc {
    return func(context *kong.Context, parent *kong.Path, flag *kong.Flag) (any, error) {
        // Get value from somewhere
        rawValue := getConfigValue(flag.Name)
        if rawValue == "" {
            return nil, nil
        }

        // Convert based on flag type
        if flag.IsBool() {
            return strconv.ParseBool(rawValue)
        }

        if flag.Value.Target.Kind() == reflect.Int {
            return strconv.Atoi(rawValue)
        }

        // Return as string for other types
        return rawValue, nil
    }
}

func getConfigValue(key string) string {
    return ""
}
```

### Using LoadConfig Method

```go
type CLI struct {
    Config kong.ConfigFlag `type:"path" help:"Load configuration from file."`

    Host string `help:"Server host."`
    Port int    `help:"Server port."`
}

func main() {
    var cli CLI

    parser := kong.Must(&cli,
        kong.Configuration(kong.JSON, "default-config.json"),
    )

    ctx, err := parser.Parse(os.Args[1:])
    parser.FatalIfErrorf(err)

    // If --config flag was provided, load that config file
    if cli.Config != "" {
        resolver, err := parser.LoadConfig(string(cli.Config))
        if err != nil {
            parser.FatalIfErrorf(err)
        }

        ctx.AddResolver(resolver)
        err = ctx.Resolve()
        ctx.FatalIfErrorf(err)
    }

    err = ctx.Run()
    ctx.FatalIfErrorf(err)
}
```
