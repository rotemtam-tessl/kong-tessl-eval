# Tags

This document covers Kong's tag system, which uses struct field tags to configure CLI behavior. Tags control everything from help text to validation and parsing behavior.

## Tag Type

Represents the parsed state of Kong tags in a struct field tag.

```go { .api }
// Tag represents the parsed state of Kong tags in a struct field tag
type Tag struct {
    // Ignored indicates the field is ignored by Kong (kong:"-")
    Ignored bool

    // Cmd indicates this is a command
    Cmd bool

    // Arg indicates this is an argument
    Arg bool

    // Required indicates this is required
    Required bool

    // Optional indicates this is optional
    Optional bool

    // Name is the field name
    Name string

    // Help is the help text
    Help string

    // Type is the type override
    Type string

    // TypeName is the actual type name
    TypeName string

    // HasDefault indicates there is a default value
    HasDefault bool

    // Default is the default value
    Default string

    // Format is the format string
    Format string

    // PlaceHolder is the placeholder text
    PlaceHolder string

    // Envs are environment variable names
    Envs []string

    // Short is the short flag character
    Short rune

    // Hidden indicates the field is hidden from help
    Hidden bool

    // Sep is the separator for slice values
    Sep rune

    // MapSep is the separator for map values
    MapSep rune

    // Enum is the enum values
    Enum string

    // Group is the group key
    Group string

    // Xor are mutually exclusive group tags
    Xor []string

    // And are mutually dependent group tags
    And []string

    // Vars are variables for interpolation
    Vars Vars

    // Prefix is the optional prefix on anonymous structs
    Prefix string

    // EnvPrefix is the environment variable prefix
    EnvPrefix string

    // XorPrefix is the optional prefix on XOR/AND groups
    XorPrefix string

    // Embed indicates this is embedded
    Embed bool

    // Aliases are aliases
    Aliases []string

    // Negatable is the negatable flag configuration
    Negatable string

    // Passthrough is deprecated: use PassthroughMode instead
    Passthrough bool

    // PassthroughMode is the passthrough mode
    PassthroughMode PassthroughMode
}
```

## Tag Methods

```go { .api }
// String returns string representation
func (t *Tag) String() string

// Has returns true if the tag contained the given key
func (t *Tag) Has(k string) bool

// Get returns the value of the given tag
func (t *Tag) Get(k string) string

// GetAll returns all encountered values for a tag
func (t *Tag) GetAll(k string) []string

// GetBool returns true if the given tag looks like a boolean truth string
func (t *Tag) GetBool(k string) (bool, error)

// GetFloat parses the given tag as a float64
func (t *Tag) GetFloat(k string) (float64, error)

// GetInt parses the given tag as an int64
func (t *Tag) GetInt(k string) (int64, error)

// GetRune parses the given tag as a rune
func (t *Tag) GetRune(k string) (rune, error)

// GetSep parses the given tag as a rune separator
func (t *Tag) GetSep(k string, dflt rune) (rune, error)
```

## PassthroughMode

Indicates how parameters are passed through when "passthrough" is set.

```go { .api }
// PassthroughMode indicates how parameters are passed through
type PassthroughMode int

const (
    // PassThroughModeNone - passthrough mode is disabled
    PassThroughModeNone PassthroughMode = 0

    // PassThroughModeAll - all parameters, including flags, are passed
    // through (default)
    PassThroughModeAll PassthroughMode = 1

    // PassThroughModePartial - validate flags until the first positional
    // argument, then pass through all remaining positional arguments
    PassThroughModePartial PassthroughMode = 2
)
```

## Common Tag Examples

### Basic Tags

```go
package main

import "github.com/alecthomas/kong"

type CLI struct {
    // Help text
    Verbose bool `help:"Enable verbose output."`

    // Short flag
    Debug bool `short:"d" help:"Enable debug mode."`

    // Default value
    Port int `help:"Port to listen on." default:"8080"`

    // Required flag
    Host string `help:"Host to bind to." required:""`

    // Hidden flag
    Secret string `help:"Secret token." hidden:""`
}

func main() {
    var cli CLI
    ctx := kong.Parse(&cli)
}
```

### Command Tags

```go
type CLI struct {
    // Command with help
    Serve struct {
        Port int `help:"Port to listen on." default:"8080"`
    } `cmd:"" help:"Start the server."`

    // Command with aliases
    Version struct{} `cmd:"" aliases:"ver,v" help:"Show version."`

    // Default command
    Run struct{} `cmd:"" default:"1" help:"Run the application."`

    // Hidden command
    Internal struct{} `cmd:"" hidden:"" help:"Internal command."`
}
```

### Argument Tags

```go
type CLI struct {
    Install struct {
        // Positional argument
        Package string `arg:"" help:"Package to install."`

        // Optional positional
        Version string `arg:"" optional:"" help:"Package version."`

        // Required positional
        Target string `arg:"" required:"" help:"Installation target."`
    } `cmd:""`
}
```

### Environment Variable Tags

```go
type CLI struct {
    // Single environment variable
    APIKey string `help:"API key." env:"API_KEY"`

    // Multiple environment variables
    Token string `help:"Auth token." env:"TOKEN,AUTH_TOKEN"`

    // With env prefix
    Database struct {
        Host string `help:"Database host." env:"HOST"`
        Port int    `help:"Database port." env:"PORT"`
    } `envprefix:"DB_"`
}

// Usage:
// --api-key=xxx or API_KEY=xxx
// --token=yyy or TOKEN=yyy or AUTH_TOKEN=yyy
// --database-host=localhost or DB_HOST=localhost
```

### Type Tags

```go
type CLI struct {
    // Path type (enables file completion)
    Config string `type:"path" help:"Configuration file."`

    // Custom type mapper
    Timeout string `type:"duration" help:"Request timeout."`

    // File content
    Certificate kong.FileContentFlag `type:"path" help:"Certificate file."`
}
```

### Enum Tags

```go
type CLI struct {
    // Enum values
    LogLevel string `help:"Log level." enum:"debug,info,warn,error" default:"info"`

    // Enum with validation
    Format string `help:"Output format." enum:"json,yaml,text" required:""`
}

// Invalid values will be rejected with an error
```

### Placeholder Tags

```go
type CLI struct {
    // Custom placeholder
    Host string `help:"Server host." placeholder:"hostname"`

    // Default placeholder
    Port int `help:"Server port."` // placeholder will be "PORT"
}

// Help output:
// --host=hostname    Server host.
// --port=PORT        Server port.
```

### Separator Tags

```go
type CLI struct {
    // Custom separator for slices
    Tags []string `help:"Tags." sep:","`

    // Custom separator for maps
    Labels map[string]string `help:"Labels." mapsep:":"`
}

// Usage:
// --tags=one,two,three
// --labels=key1:val1 --labels=key2:val2
```

### Group Tags

```go
type CLI struct {
    // Flags in the same group
    Verbose bool `help:"Verbose output." group:"output"`
    Quiet   bool `help:"Quiet output." group:"output"`
    Format  string `help:"Output format." group:"output"`

    Debug   bool `help:"Enable debug." group:"debug"`
    Profile bool `help:"Enable profiling." group:"debug"`
}

func main() {
    var cli CLI
    ctx := kong.Parse(&cli,
        kong.ExplicitGroups([]kong.Group{
            {Key: "output", Title: "Output Options:"},
            {Key: "debug", Title: "Debug Options:"},
        }),
    )
}
```

### Validation Tags

```go
type CLI struct {
    // Mutually exclusive flags
    JSON bool `help:"JSON output." xor:"format"`
    YAML bool `help:"YAML output." xor:"format"`
    Text bool `help:"Text output." xor:"format"`

    // Mutually dependent flags
    Username string `help:"Username." and:"auth"`
    Password string `help:"Password." and:"auth"`
}

// Usage:
// Can specify --json OR --yaml OR --text (not multiple)
// Must specify both --username AND --password (or neither)
```

### Prefix Tags

```go
type ServerConfig struct {
    Host string `help:"Server host."`
    Port int    `help:"Server port."`
}

type CLI struct {
    // Prefix for nested struct
    Server ServerConfig `prefix:"srv-"`
}

// Generates flags:
// --srv-host
// --srv-port
```

### Embed Tags

```go
type CommonFlags struct {
    Verbose bool `help:"Verbose output."`
    Debug   bool `help:"Debug mode."`
}

type CLI struct {
    // Embed flags without prefix
    CommonFlags `embed:""`

    Serve struct{} `cmd:""`
}

// Generates:
// --verbose
// --debug
// (not --common-flags-verbose)
```

### Negatable Flags

```go
type CLI struct {
    // Boolean flag that can be negated
    Color bool `help:"Enable colored output." negatable:"" default:"true"`
}

// Usage:
// --color       (sets to true)
// --no-color    (sets to false)
```

### Format Tags

```go
type CLI struct {
    // Custom format string for help
    Port int `help:"Port to listen on." format:"port number"`
}
```

### Passthrough Tags

```go
type CLI struct {
    Run struct {
        // Pass all remaining args to the command
        Args []string `arg:"" optional:"" passthrough:""`
    } `cmd:""`
}

// Usage:
// myapp run --flag1 --flag2 arg1 arg2
// Args will contain: ["--flag1", "--flag2", "arg1", "arg2"]
```

### Passthrough Modes

```go
type CLI struct {
    Run struct {
        // Passthrough all parameters including flags
        Args []string `arg:"" optional:"" passthrough:"all"`
    } `cmd:""`

    Exec struct {
        // Validate flags, then passthrough positionals
        Command string   `arg:"" help:"Command to execute."`
        Args    []string `arg:"" optional:"" passthrough:"partial"`
    } `cmd:""`
}

// With "all":
// myapp run --my-flag value other args
// Args: ["--my-flag", "value", "other", "args"]

// With "partial":
// myapp exec --valid-flag ls -la /tmp
// Command: "ls"
// Args: ["-la", "/tmp"]
```

### Ignored Fields

```go
type CLI struct {
    // Regular field
    Verbose bool `help:"Verbose output."`

    // Ignored by Kong
    internal string `kong:"-"`

    // Also ignored (unexported)
    state *State
}

type State struct {
    // Internal state
}
```

### Aliases

```go
type CLI struct {
    // Flag with aliases
    Verbose bool `short:"v" aliases:"verb" help:"Verbose output."`

    // Command with aliases
    Version struct{} `cmd:"" aliases:"ver,v" help:"Show version."`
}

// Usage:
// --verbose, -v, --verb (all work)
// version, ver, v (all work)
```

### Variable Interpolation

```go
type CLI struct {
    // Interpolate variables in help
    Config string `help:"Config file (default: ${config_file})." default:"${config_file}"`

    // Interpolate in defaults
    Port int `help:"Port to listen on." default:"${default_port}"`
}

func main() {
    var cli CLI
    ctx := kong.Parse(&cli,
        kong.Vars{
            "config_file":  "/etc/myapp.conf",
            "default_port": "8080",
        },
    )
}
```

### Tag Vars

```go
type CLI struct {
    // Define vars in the tag itself
    Serve struct {
        Port int `help:"Port (default: ${port})." default:"${port}" vars:"port=8080"`
    } `cmd:""`
}
```

### XOR and AND Prefixes

```go
type ServerConfig struct {
    HTTP  bool `xor:"protocol"`
    HTTPS bool `xor:"protocol"`
}

type CLI struct {
    Server ServerConfig `xorprefix:"srv-"`
}

// Creates xor groups:
// srv-protocol (containing HTTP and HTTPS)
```

### Complete Example

```go
type CLI struct {
    // Global flags with various tags
    Verbose bool   `short:"v" help:"Enable verbose output." group:"output"`
    Quiet   bool   `short:"q" help:"Quiet mode." xor:"verbosity" group:"output"`
    Debug   bool   `short:"d" help:"Debug mode." env:"DEBUG" hidden:""`
    Config  string `type:"path" help:"Config file." placeholder:"PATH" default:"${config}"`

    // Command with full configuration
    Serve struct {
        // Flags
        Host string `help:"Host to bind to." default:"localhost" placeholder:"HOST"`
        Port int    `help:"Port to listen on." short:"p" default:"8080" env:"PORT"`

        // Validation
        TLS  bool   `help:"Enable TLS." xor:"security"`
        HTTP bool   `help:"HTTP only." xor:"security" default:"true"`

        // Positional args
        Root string `arg:"" type:"path" help:"Root directory." default:"."`
    } `cmd:"" help:"Start the server." aliases:"s,srv"`

    // Version command
    Version struct{} `cmd:"" help:"Show version." aliases:"ver,v"`
}

func main() {
    var cli CLI
    ctx := kong.Parse(&cli,
        kong.Name("myapp"),
        kong.Vars{"config": "/etc/myapp.conf"},
        kong.ExplicitGroups([]kong.Group{
            {Key: "output", Title: "Output Options:"},
        }),
    )

    err := ctx.Run()
    ctx.FatalIfErrorf(err)
}
```

## Working with Tag Fields

While Kong automatically parses struct tags, you can also access tag information programmatically:

```go
func examineTag(tag *kong.Tag) {
    fmt.Printf("Name: %s\n", tag.Name)
    fmt.Printf("Help: %s\n", tag.Help)
    fmt.Printf("Required: %v\n", tag.Required)

    if tag.HasDefault {
        fmt.Printf("Default: %s\n", tag.Default)
    }

    if tag.Short != 0 {
        fmt.Printf("Short: -%c\n", tag.Short)
    }

    if tag.Enum != "" {
        fmt.Printf("Enum: %s\n", tag.Enum)
    }

    // Check for specific tags
    if tag.Has("group") {
        fmt.Printf("Group: %s\n", tag.Get("group"))
    }

    // Get all values for a repeated tag
    envs := tag.GetAll("env")
    fmt.Printf("Environment vars: %v\n", envs)
}
```
