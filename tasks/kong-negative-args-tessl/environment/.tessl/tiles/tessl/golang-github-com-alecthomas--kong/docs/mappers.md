# Type Mappers

This document covers Kong's type mapping system, which converts command-line string arguments into Go types. Mappers handle everything from built-in types to custom types.

## Core Mapper Interfaces

### Mapper

The primary interface for type mapping.

```go { .api }
// Mapper represents how a field is mapped from command-line values to Go
type Mapper interface {
    Decode(ctx *DecodeContext, target reflect.Value) error
}

// MapperFunc is a single function that complies with the Mapper interface
type MapperFunc func(ctx *DecodeContext, target reflect.Value) error
```

### MapperValue

Interface that may be implemented by fields to provide custom mapping.

```go { .api }
// MapperValue may be implemented by fields to provide custom mapping
type MapperValue interface {
    Decode(ctx *DecodeContext) error
}
```

### BoolMapper and BoolMapperValue

Special interfaces for boolean types.

```go { .api }
// BoolMapperValue may be implemented by fields to provide custom mappings
// for boolean values
type BoolMapperValue interface {
    Decode(ctx *DecodeContext) error
    IsBool() bool
}

// BoolMapper is a Mapper to a value that is a boolean
// (used solely for formatting help)
type BoolMapper interface {
    Decode(ctx *DecodeContext, target reflect.Value) error
    IsBool() bool
}

// BoolMapperExt allows a Mapper to dynamically determine if a value
// is a boolean
type BoolMapperExt interface {
    Decode(ctx *DecodeContext, target reflect.Value) error
    IsBoolFromValue(v reflect.Value) bool
}
```

### VarsContributor

Interface for mappers that contribute variables during interpolation.

```go { .api }
// VarsContributor can be implemented by a Mapper to contribute Vars
// during interpolation
type VarsContributor interface {
    Vars(ctx *Value) Vars
}
```

## DecodeContext

Context passed to a Mapper's Decode() method.

```go { .api }
// DecodeContext is passed to a Mapper's Decode()
type DecodeContext struct {
    // Value being decoded into
    Value *Value

    // Scanner containing the input
    Scan *Scanner
}

// WithScanner creates a clone with a new Scanner
func (d *DecodeContext) WithScanner(scan *Scanner) *DecodeContext
```

## Registry

Registry contains a set of mappers and methods for looking them up.

```go { .api }
// Registry contains a set of mappers and supporting lookup methods
type Registry struct {
    // Internal fields not exported
}

// NewRegistry creates a new empty Registry for type mappers
func NewRegistry() *Registry
```

### Registry Methods

```go { .api }
// ForNamedValue finds a mapper for a value with a user-specified name
func (r *Registry) ForNamedValue(name string, value reflect.Value) Mapper

// ForValue looks up the Mapper for a reflect.Value
func (r *Registry) ForValue(value reflect.Value) Mapper

// ForNamedType finds a mapper for a type with a user-specified name
func (r *Registry) ForNamedType(name string, typ reflect.Type) Mapper

// ForType finds a mapper from a type, by type, then kind
func (r *Registry) ForType(typ reflect.Type) Mapper

// RegisterKind registers a Mapper for a reflect.Kind
func (r *Registry) RegisterKind(kind reflect.Kind, mapper Mapper) *Registry

// RegisterName registers a mapper to be used if the value mapper has
// a "type" tag matching name
func (r *Registry) RegisterName(name string, mapper Mapper) *Registry

// RegisterType registers a Mapper for a reflect.Type
func (r *Registry) RegisterType(typ reflect.Type, mapper Mapper) *Registry

// RegisterValue registers a Mapper by pointer to the field value
func (r *Registry) RegisterValue(ptr any, mapper Mapper) *Registry

// RegisterDefaults registers Mappers for all builtin supported Go types
func (r *Registry) RegisterDefaults() *Registry
```

## File Content Flags

Special flag types for reading file contents.

```go { .api }
// NamedFileContentFlag is a flag value that loads a file's contents
// and filename into its value
type NamedFileContentFlag struct {
    Filename string
    Contents []byte
}

// Decode loads the file contents
func (f *NamedFileContentFlag) Decode(ctx *DecodeContext) error

// FileContentFlag is a flag value that loads a file's contents into its value
type FileContentFlag []byte

// Decode loads the file contents
func (f *FileContentFlag) Decode(ctx *DecodeContext) error
```

## Utility Functions

```go { .api }
// SplitEscaped splits a string on a separator, allowing the separator
// to exist in a field by escaping it with a backslash
func SplitEscaped(s string, sep rune) []string

// JoinEscaped joins a slice of strings on sep, escaping any instances
// of sep in the fields with backslash
func JoinEscaped(s []string, sep rune) string
```

## Usage Examples

### Implementing a Custom Mapper

```go
package main

import (
    "fmt"
    "net"
    "reflect"
    "github.com/alecthomas/kong"
)

// Custom type for IP addresses
type IPAddr net.IP

// Implement MapperValue interface
func (i *IPAddr) Decode(ctx *kong.DecodeContext) error {
    var s string
    if err := ctx.Scan.PopValueInto("ip", &s); err != nil {
        return err
    }

    ip := net.ParseIP(s)
    if ip == nil {
        return fmt.Errorf("invalid IP address: %s", s)
    }

    *i = IPAddr(ip)
    return nil
}

type CLI struct {
    Server IPAddr `help:"Server IP address."`
}

func main() {
    var cli CLI
    ctx := kong.Parse(&cli)

    fmt.Printf("Server IP: %s\n", net.IP(cli.Server))
}
```

### Using MapperFunc

```go
import (
    "time"
    "reflect"
)

func durationMapper() kong.MapperFunc {
    return func(ctx *kong.DecodeContext, target reflect.Value) error {
        var s string
        if err := ctx.Scan.PopValueInto("duration", &s); err != nil {
            return err
        }

        d, err := time.ParseDuration(s)
        if err != nil {
            return fmt.Errorf("invalid duration: %w", err)
        }

        target.Set(reflect.ValueOf(d))
        return nil
    }
}

type CLI struct {
    Timeout time.Duration `help:"Request timeout."`
}

func main() {
    var cli CLI

    parser := kong.Must(&cli,
        kong.TypeMapper(reflect.TypeOf(time.Duration(0)), durationMapper()),
    )

    ctx, err := parser.Parse(os.Args[1:])
    parser.FatalIfErrorf(err)
}
```

### Custom Registry

```go
func main() {
    registry := kong.NewRegistry().RegisterDefaults()

    // Register custom mapper for URL type
    registry.RegisterType(reflect.TypeOf(&url.URL{}), kong.MapperFunc(
        func(ctx *kong.DecodeContext, target reflect.Value) error {
            var s string
            if err := ctx.Scan.PopValueInto("url", &s); err != nil {
                return err
            }

            u, err := url.Parse(s)
            if err != nil {
                return fmt.Errorf("invalid URL: %w", err)
            }

            target.Set(reflect.ValueOf(u))
            return nil
        },
    ))

    // Use registry with parser
    // (typically done via TypeMapper option instead)
}
```

### Boolean Mapper

```go
type FeatureFlag struct {
    enabled bool
}

func (f *FeatureFlag) Decode(ctx *kong.DecodeContext) error {
    // Peek to see if there's a value
    token := ctx.Scan.Peek()

    if token.IsValue() {
        var s string
        if err := ctx.Scan.PopValueInto("feature", &s); err != nil {
            return err
        }

        switch s {
        case "on", "true", "yes", "1":
            f.enabled = true
        case "off", "false", "no", "0":
            f.enabled = false
        default:
            return fmt.Errorf("invalid feature flag value: %s", s)
        }
    } else {
        // No value provided, treat as true
        f.enabled = true
    }

    return nil
}

func (f *FeatureFlag) IsBool() bool {
    return true
}

type CLI struct {
    Feature FeatureFlag `help:"Enable feature."`
}

func main() {
    var cli CLI
    ctx := kong.Parse(&cli)

    // Can be used as:
    // --feature
    // --feature=on
    // --feature=off
}
```

### File Content Flags

```go
type CLI struct {
    // Load file contents into byte slice
    Certificate kong.FileContentFlag `help:"Certificate file." type:"path"`

    // Load file contents and track filename
    Config kong.NamedFileContentFlag `help:"Config file." type:"path"`
}

func main() {
    var cli CLI
    ctx := kong.Parse(&cli)

    // cli.Certificate contains the file contents
    fmt.Printf("Certificate size: %d bytes\n", len(cli.Certificate))

    // cli.Config contains both filename and contents
    fmt.Printf("Config file: %s\n", cli.Config.Filename)
    fmt.Printf("Config size: %d bytes\n", len(cli.Config.Contents))
}
```

### Named Type Mapper

```go
type DatabaseURL string

func (d *DatabaseURL) Validate() error {
    // Custom validation
    if !strings.HasPrefix(string(*d), "postgres://") {
        return fmt.Errorf("must be a PostgreSQL URL")
    }
    return nil
}

type CLI struct {
    // Use named mapper via type tag
    Database string `help:"Database URL." type:"database-url"`
}

func main() {
    var cli CLI

    parser := kong.Must(&cli,
        kong.NamedMapper("database-url", kong.MapperFunc(
            func(ctx *kong.DecodeContext, target reflect.Value) error {
                var s string
                if err := ctx.Scan.PopValueInto("url", &s); err != nil {
                    return err
                }

                // Parse and validate
                if !strings.HasPrefix(s, "postgres://") {
                    return fmt.Errorf("must be a PostgreSQL URL")
                }

                target.SetString(s)
                return nil
            },
        )),
    )

    ctx, err := parser.Parse(os.Args[1:])
    parser.FatalIfErrorf(err)
}
```

### Slice Mapper with Custom Separator

```go
type CommaSeparatedStrings []string

func (c *CommaSeparatedStrings) Decode(ctx *kong.DecodeContext) error {
    var s string
    if err := ctx.Scan.PopValueInto("strings", &s); err != nil {
        return err
    }

    // Use SplitEscaped to allow escaped commas
    *c = kong.SplitEscaped(s, ',')
    return nil
}

type CLI struct {
    Tags CommaSeparatedStrings `help:"Comma-separated tags."`
}

func main() {
    var cli CLI
    ctx := kong.Parse(&cli)

    // Usage: --tags="one,two,three\,with\,commas,four"
    // Result: ["one", "two", "three,with,commas", "four"]
    fmt.Printf("Tags: %v\n", cli.Tags)
}
```

### Map Mapper

```go
type KeyValueMap map[string]string

func (k *KeyValueMap) Decode(ctx *kong.DecodeContext) error {
    if *k == nil {
        *k = make(map[string]string)
    }

    var s string
    if err := ctx.Scan.PopValueInto("key=value", &s); err != nil {
        return err
    }

    parts := strings.SplitN(s, "=", 2)
    if len(parts) != 2 {
        return fmt.Errorf("expected key=value format, got %s", s)
    }

    (*k)[parts[0]] = parts[1]
    return nil
}

type CLI struct {
    Labels KeyValueMap `help:"Labels as key=value pairs."`
}

func main() {
    var cli CLI
    ctx := kong.Parse(&cli)

    // Usage: --labels=env=prod --labels=region=us-east
    // Result: map[env:prod region:us-east]
    fmt.Printf("Labels: %v\n", cli.Labels)
}
```

### Vars Contributor

```go
type ConfigFile struct {
    path string
    vars map[string]string
}

func (c *ConfigFile) Decode(ctx *kong.DecodeContext) error {
    var s string
    if err := ctx.Scan.PopValueInto("path", &s); err != nil {
        return err
    }

    c.path = s

    // Load config file and extract variables
    data, err := os.ReadFile(s)
    if err != nil {
        return err
    }

    // Parse config and extract vars
    c.vars = parseConfigVars(data)
    return nil
}

func (c *ConfigFile) Vars(ctx *kong.Value) kong.Vars {
    // Contribute loaded variables for interpolation
    return c.vars
}

func parseConfigVars(data []byte) map[string]string {
    // Implementation to parse config and extract vars
    return nil
}
```

### Value Mapper Registration

```go
type CLI struct {
    // Specific field gets custom mapper
    Special string `help:"Special field."`
}

func main() {
    var cli CLI

    parser := kong.Must(&cli,
        // Map specific field by pointer
        kong.ValueMapper(&cli.Special, kong.MapperFunc(
            func(ctx *kong.DecodeContext, target reflect.Value) error {
                var s string
                if err := ctx.Scan.PopValueInto("special", &s); err != nil {
                    return err
                }

                // Custom processing for this specific field
                target.SetString(strings.ToUpper(s))
                return nil
            },
        )),
    )

    ctx, err := parser.Parse(os.Args[1:])
    parser.FatalIfErrorf(err)
}
```

### Kind Mapper

```go
func main() {
    var cli CLI

    parser := kong.Must(&cli,
        // Register mapper for all uint types
        kong.KindMapper(reflect.Uint, kong.MapperFunc(
            func(ctx *kong.DecodeContext, target reflect.Value) error {
                var s string
                if err := ctx.Scan.PopValueInto("uint", &s); err != nil {
                    return err
                }

                // Custom parsing for uint
                val, err := strconv.ParseUint(s, 0, 64)
                if err != nil {
                    return err
                }

                target.SetUint(val)
                return nil
            },
        )),
    )

    ctx, err := parser.Parse(os.Args[1:])
    parser.FatalIfErrorf(err)
}
```
