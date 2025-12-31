# Configuration Options

This document covers Kong's extensive configuration options that customize parser behavior, appearance, and functionality.

## Option Interface

```go { .api }
// Option applies optional changes to the Kong application
type Option interface {
    Apply(k *Kong) error
}

// OptionFunc is a function type that adheres to the Option interface
type OptionFunc func(k *Kong) error
```

## Configuration Types

### Vars

Sets the variables to use for interpolation into help strings and default values.

```go { .api }
// Vars is a map of variables for interpolation
type Vars map[string]string

// Apply lets Vars act as an Option
func (v Vars) Apply(k *Kong) error

// CloneWith clones the current Vars and merges "vars" onto the clone
func (v Vars) CloneWith(vars Vars) Vars
```

### Groups

Associates group field tags with group metadata.

```go { .api }
// Groups is a map associating group field tags with group metadata
type Groups map[string]string

// Apply lets Groups act as an Option
func (g Groups) Apply(k *Kong) error
```

### ConfigurationLoader

A function that builds a resolver from a file.

```go { .api }
// ConfigurationLoader is a function that builds a resolver from a file
type ConfigurationLoader func(r io.Reader) (Resolver, error)
```

## Basic Options

### Application Metadata

```go { .api }
// Name overrides the application name
func Name(name string) Option

// Description sets the application description
func Description(description string) Option
```

### Input/Output

```go { .api }
// Writers overrides the default writers (useful for testing or interactive use)
func Writers(stdout, stderr io.Writer) Option

// Exit overrides the function used to terminate (useful for testing or interactive use)
func Exit(exit func(int)) Option
```

### Help System

```go { .api }
// NoDefaultHelp disables the default help flags
func NoDefaultHelp() Option

// Help sets the help printer to use
func Help(help HelpPrinter) Option

// ShortHelp configures the short usage message
func ShortHelp(shortHelp HelpPrinter) Option

// HelpFormatter is deprecated: Use ValueFormatter() instead
// Configures how the help text is formatted
func HelpFormatter(helpFormatter HelpValueFormatter) Option

// ValueFormatter configures how the help text is formatted
func ValueFormatter(helpFormatter HelpValueFormatter) Option

// ConfigureHelp sets the HelpOptions to use for printing help
func ConfigureHelp(options HelpOptions) Option
```

### Error Handling

```go { .api }
// UsageOnError configures Kong to display context-sensitive usage if
// FatalIfErrorf is called with an error
func UsageOnError() Option

// ShortUsageOnError configures Kong to display context-sensitive short
// usage if FatalIfErrorf is called with an error
func ShortUsageOnError() Option
```

## Type Mapping Options

```go { .api }
// TypeMapper registers a mapper to a type
func TypeMapper(typ reflect.Type, mapper Mapper) Option

// KindMapper registers a mapper to a kind
func KindMapper(kind reflect.Kind, mapper Mapper) Option

// ValueMapper registers a mapper to a field value
func ValueMapper(ptr any, mapper Mapper) Option

// NamedMapper registers a mapper to a name
func NamedMapper(name string, mapper Mapper) Option
```

## Binding and Dependency Injection

```go { .api }
// Bind binds values for hooks and Run() function arguments
func Bind(args ...any) Option

// BindTo allows binding of implementations to interfaces
func BindTo(impl, iface any) Option

// BindToProvider binds an injected value to a provider function
func BindToProvider(provider any) Option

// BindSingletonProvider binds an injected value to a singleton provider function
func BindSingletonProvider(provider any) Option
```

## Resolver Options

```go { .api }
// ClearResolvers clears all existing resolvers
func ClearResolvers() Option

// Resolvers registers flag resolvers
func Resolvers(resolvers ...Resolver) Option

// Configuration provides Kong with support for loading defaults from
// a set of configuration files
func Configuration(loader ConfigurationLoader, paths ...string) Option

// DefaultEnvars inits environment names for flags
// (e.g., --some.value -> PREFIX_SOME_VALUE)
func DefaultEnvars(prefix string) Option
```

## Hook Options

```go { .api }
// WithBeforeReset registers a hook to run before fields values are
// reset to their defaults
func WithBeforeReset(fn any) Option

// WithBeforeResolve registers a hook to run before resolvers are applied
func WithBeforeResolve(fn any) Option

// WithBeforeApply registers a hook to run before command line arguments are applied
func WithBeforeApply(fn any) Option

// WithAfterApply registers a hook to run after values are applied and validated
func WithAfterApply(fn any) Option
```

## Advanced Structure Options

```go { .api }
// Embed embeds a struct into the root of the CLI
func Embed(strct any, tags ...string) Option

// DynamicCommand registers a dynamically constructed command with the
// root of the CLI
func DynamicCommand(name, help, group string, cmd any, tags ...string) Option

// WithHyphenPrefixedParameters(true) enables parsing negative numbers
// and hyphen-prefixed strings as flag values instead of short flags.
// Default is false (hyphen starts a new flag).
func WithHyphenPrefixedParameters(enable bool) Option

// IgnoreFields causes kong.New() to skip field names that match any
// of the provided regex patterns
func IgnoreFields(regexes ...string) Option

// PostBuild provides read/write access to kong.Kong after initial construction
func PostBuild(fn func(*Kong) error) Option
```

## Grouping Options

```go { .api }
// AutoGroup automatically assigns groups to flags
func AutoGroup(format func(parent Visitable, flag *Flag) *Group) Option

// ExplicitGroups associates group field tags with their metadata
func ExplicitGroups(groups []Group) Option
```

## Naming Options

```go { .api }
// FlagNamer allows you to override the default kebab-case automated
// flag name generation
func FlagNamer(namer func(fieldName string) string) Option
```

## Usage Examples

### Basic Configuration

```go
package main

import (
    "os"
    "github.com/alecthomas/kong"
)

type CLI struct {
    Debug bool `help:"Enable debug mode."`
}

func main() {
    var cli CLI

    parser := kong.Must(&cli,
        kong.Name("myapp"),
        kong.Description("A simple application"),
        kong.UsageOnError(),
    )

    ctx, err := parser.Parse(os.Args[1:])
    parser.FatalIfErrorf(err)
}
```

### Custom Help Configuration

```go
func main() {
    var cli CLI

    parser := kong.Must(&cli,
        kong.ConfigureHelp(kong.HelpOptions{
            Compact:      true,
            Tree:         true,
            NoAppSummary: false,
        }),
    )

    ctx, err := parser.Parse(os.Args[1:])
    parser.FatalIfErrorf(err)
}
```

### Variable Interpolation

```go
type CLI struct {
    Config string `help:"Config file location." default:"${config_dir}/app.conf"`
    Port   int    `help:"Port to listen on." default:"${default_port}"`
}

func main() {
    var cli CLI

    parser := kong.Must(&cli,
        kong.Vars{
            "config_dir":   "/etc/myapp",
            "default_port": "8080",
        },
    )

    ctx, err := parser.Parse(os.Args[1:])
    parser.FatalIfErrorf(err)

    // cli.Config will be "/etc/myapp/app.conf" if not overridden
    // cli.Port will be 8080 if not overridden
}
```

### Environment Variable Support

```go
type CLI struct {
    APIKey string `help:"API key for service." env:"API_KEY"`
    Debug  bool   `help:"Enable debug mode." env:"DEBUG"`
}

func main() {
    var cli CLI

    // Automatically map flags to environment variables with prefix
    parser := kong.Must(&cli,
        kong.DefaultEnvars("MYAPP"),
    )

    ctx, err := parser.Parse(os.Args[1:])
    parser.FatalIfErrorf(err)

    // Now flags can be set via:
    // - Command line: --api-key=xxx
    // - Environment: MYAPP_API_KEY=xxx or API_KEY=xxx (from env tag)
}
```

### Configuration File Support

```go
type CLI struct {
    Config string `type:"path" help:"Load configuration from file."`

    Host string `help:"Server host."`
    Port int    `help:"Server port."`
}

func main() {
    var cli CLI

    parser := kong.Must(&cli,
        kong.Configuration(kong.JSON, "config.json", "~/.myapp.json"),
    )

    ctx, err := parser.Parse(os.Args[1:])
    parser.FatalIfErrorf(err)

    // Will load from config.json or ~/.myapp.json if they exist
    // Command-line flags override config file values
}
```

### Dependency Injection

```go
type Database struct {
    conn *sql.DB
}

type CLI struct {
    Serve struct {
        Port int `help:"Port to listen on." default:"8080"`
    } `cmd:""`
}

func (s *Serve) Run(db *Database) error {
    fmt.Printf("Starting server on port %d with database\n", s.Port)
    // Use db connection
    return nil
}

func main() {
    var cli CLI

    // Create database connection
    db := &Database{
        // Initialize connection
    }

    parser := kong.Must(&cli,
        kong.Bind(db),
    )

    ctx, err := parser.Parse(os.Args[1:])
    parser.FatalIfErrorf(err)

    // Database will be injected into Run() method
    err = ctx.Run()
    ctx.FatalIfErrorf(err)
}
```

### Interface Binding

```go
type Logger interface {
    Log(msg string)
}

type ConsoleLogger struct{}

func (c *ConsoleLogger) Log(msg string) {
    fmt.Println(msg)
}

type CLI struct {
    Serve struct{} `cmd:""`
}

func (s *Serve) Run(logger Logger) error {
    logger.Log("Starting server")
    return nil
}

func main() {
    var cli CLI
    logger := &ConsoleLogger{}

    parser := kong.Must(&cli,
        kong.BindTo(logger, (*Logger)(nil)),
    )

    ctx, err := parser.Parse(os.Args[1:])
    parser.FatalIfErrorf(err)

    err = ctx.Run()
    ctx.FatalIfErrorf(err)
}
```

### Provider Functions

```go
type Config struct {
    DatabaseURL string
}

// Provider function that returns a config
func provideConfig() (*Config, error) {
    return &Config{
        DatabaseURL: "postgres://localhost/mydb",
    }, nil
}

func (s *Serve) Run(config *Config) error {
    fmt.Printf("Using database: %s\n", config.DatabaseURL)
    return nil
}

func main() {
    var cli CLI

    parser := kong.Must(&cli,
        kong.BindToProvider(provideConfig),
    )

    ctx, err := parser.Parse(os.Args[1:])
    parser.FatalIfErrorf(err)

    err = ctx.Run()
    ctx.FatalIfErrorf(err)
}
```

### Custom Type Mappers

```go
type Duration time.Duration

func durationMapper() kong.MapperFunc {
    return func(ctx *kong.DecodeContext, target reflect.Value) error {
        var str string
        if err := ctx.Scan.PopValueInto("duration", &str); err != nil {
            return err
        }
        d, err := time.ParseDuration(str)
        if err != nil {
            return err
        }
        target.Set(reflect.ValueOf(Duration(d)))
        return nil
    }
}

type CLI struct {
    Timeout Duration `help:"Request timeout."`
}

func main() {
    var cli CLI

    parser := kong.Must(&cli,
        kong.TypeMapper(reflect.TypeOf(Duration(0)), durationMapper()),
    )

    ctx, err := parser.Parse(os.Args[1:])
    parser.FatalIfErrorf(err)
}
```

### Explicit Groups

```go
type CLI struct {
    Verbose bool   `help:"Verbose output." group:"output"`
    Quiet   bool   `help:"Quiet output." group:"output"`
    Format  string `help:"Output format." group:"output"`

    Debug   bool `help:"Enable debug." group:"debug"`
    Profile bool `help:"Enable profiling." group:"debug"`
}

func main() {
    var cli CLI

    parser := kong.Must(&cli,
        kong.ExplicitGroups([]kong.Group{
            {
                Key:         "output",
                Title:       "Output Options:",
                Description: "Control output formatting and verbosity",
            },
            {
                Key:         "debug",
                Title:       "Debug Options:",
                Description: "Development and debugging features",
            },
        }),
    )

    ctx, err := parser.Parse(os.Args[1:])
    parser.FatalIfErrorf(err)
}
```

### Dynamic Commands

```go
type PluginCmd struct {
    Name string `arg:"" help:"Plugin name."`
}

func (p *PluginCmd) Run() error {
    fmt.Printf("Running plugin: %s\n", p.Name)
    return nil
}

func main() {
    var cli CLI

    parser := kong.Must(&cli,
        kong.DynamicCommand(
            "plugin",
            "Execute a plugin",
            "plugins",
            &PluginCmd{},
        ),
    )

    ctx, err := parser.Parse(os.Args[1:])
    parser.FatalIfErrorf(err)

    err = ctx.Run()
    ctx.FatalIfErrorf(err)
}
```

### Post-Build Hook

```go
func main() {
    var cli CLI

    parser := kong.Must(&cli,
        kong.PostBuild(func(k *kong.Kong) error {
            // Modify the model after construction
            for _, flag := range k.Model.Flags {
                if flag.Name == "debug" {
                    flag.Hidden = true
                }
            }
            return nil
        }),
    )

    ctx, err := parser.Parse(os.Args[1:])
    parser.FatalIfErrorf(err)
}
```

### Custom I/O for Testing

```go
func TestCLI(t *testing.T) {
    var cli CLI
    var stdout, stderr bytes.Buffer

    parser := kong.Must(&cli,
        kong.Writers(&stdout, &stderr),
        kong.Exit(func(code int) {
            t.Logf("Would exit with code %d", code)
        }),
    )

    ctx, err := parser.Parse([]string{"--help"})
    if err != nil {
        t.Fatal(err)
    }

    // Check captured output
    output := stdout.String()
    if !strings.Contains(output, "Usage:") {
        t.Error("Help output missing")
    }
}
```
