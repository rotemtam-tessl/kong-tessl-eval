# Model Types

This document covers the types that represent Kong's parsed CLI structure, including the application model, nodes, values, flags, and groups.

## Core Model Types

### Application

The root of the Kong model.

```go { .api }
// Application is the root of the Kong model
type Application struct {
    *Node  // Embedded Node

    // HelpFlag is the help flag, if the NoDefaultHelp() option is not specified
    HelpFlag *Flag
}
```

### Node

A branch in the CLI (i.e., a command or positional argument).

```go { .api }
// Node is a branch in the CLI (i.e., a command or positional argument)
type Node struct {
    // Type is the node type (ApplicationNode, CommandNode, ArgumentNode)
    Type NodeType

    // Parent is the parent node
    Parent *Node

    // Name is the node name
    Name string

    // Help is short help displayed in summaries
    Help string

    // Detail is detailed help displayed when describing command/arg alone
    Detail string

    // Group is the group metadata
    Group *Group

    // Hidden indicates the node is hidden from help
    Hidden bool

    // Flags for this node
    Flags []*Flag

    // Positional arguments
    Positional []*Positional

    // Children nodes
    Children []*Node

    // DefaultCmd is the default command
    DefaultCmd *Node

    // Target is a pointer to the value in the grammar
    Target reflect.Value

    // Tag is the parsed tag
    Tag *Tag

    // Aliases are command aliases
    Aliases []string

    // Passthrough is set to true to stop flag parsing when encountered
    Passthrough bool

    // Active denotes the node is part of an active branch
    Active bool

    // Argument is populated when Type is ArgumentNode
    Argument *Value
}
```

### Node Methods

```go { .api }
// Leaf returns true if this Node is a leaf node
func (n *Node) Leaf() bool

// Find finds a command/argument/flag by pointer to its field
func (n *Node) Find(ptr any) *Node

// AllFlags returns flags from all ancestor branches
func (n *Node) AllFlags(hide bool) [][]*Flag

// Leaves returns the leaf commands/arguments under Node
func (n *Node) Leaves(hide bool) []*Node

// Depth returns depth of the command from the application root
func (n *Node) Depth() int

// Summary returns summary help string for the node
func (n *Node) Summary() string

// FlagSummary returns flag summary for the node
func (n *Node) FlagSummary(hide bool) string

// FullPath is like Path() but includes the Application root node
func (n *Node) FullPath() string

// Vars returns the combined Vars defined by all ancestors
func (n *Node) Vars() Vars

// Path returns path through ancestors to this Node
func (n *Node) Path() string

// ClosestGroup finds the first non-nil group in this node and its ancestors
func (n *Node) ClosestGroup() *Group
```

### NodeType

Represents the type of a Node.

```go { .api }
// NodeType represents the type of a Node
type NodeType int

const (
    // ApplicationNode is the node type for application root
    ApplicationNode NodeType = 0

    // CommandNode is the node type for commands
    CommandNode NodeType = 1

    // ArgumentNode is the node type for arguments
    ArgumentNode NodeType = 2
)
```

## Value Type

Either a flag or a variable positional argument.

```go { .api }
// Value is either a flag or a variable positional argument
type Value struct {
    // Flag is nil if this is a positional argument
    Flag *Flag

    // Name is the name of the value
    Name string

    // Help is the help text
    Help string

    // OrigHelp is the original help string, without interpolated variables
    OrigHelp string

    // HasDefault indicates if there is a default value
    HasDefault bool

    // Default is the default value as string
    Default string

    // DefaultValue is the default value as reflect.Value
    DefaultValue reflect.Value

    // Enum is comma-separated enum values
    Enum string

    // Mapper is the type mapper
    Mapper Mapper

    // Tag is the parsed tag
    Tag *Tag

    // Target is the target field
    Target reflect.Value

    // Required indicates this is a required value
    Required bool

    // Set is set to true when this value is set
    Set bool

    // Format is the formatting directive, if applicable
    Format string

    // Position is the position (for positional arguments)
    Position int

    // Passthrough is deprecated: Use PassthroughMode instead
    Passthrough bool

    // PassthroughMode is the passthrough mode
    PassthroughMode PassthroughMode

    // Active denotes the value is part of an active branch
    Active bool
}
```

### Value Methods

```go { .api }
// EnumMap returns a map of the enums in this value
func (v *Value) EnumMap() map[string]bool

// EnumSlice returns a slice of the enums in this value
func (v *Value) EnumSlice() []string

// ShortSummary returns a human-readable summary (not including placeholders/defaults)
func (v *Value) ShortSummary() string

// Summary returns a human-readable summary
func (v *Value) Summary() string

// IsCumulative returns true if the type can be accumulated into
func (v *Value) IsCumulative() bool

// IsSlice returns true if the value is a slice
func (v *Value) IsSlice() bool

// IsMap returns true if the value is a map
func (v *Value) IsMap() bool

// IsBool returns true if the underlying value is a boolean
func (v *Value) IsBool() bool

// IsCounter returns true if the value is a counter
func (v *Value) IsCounter() bool

// Parse parses tokens into value
func (v *Value) Parse(scan *Scanner, target reflect.Value) error

// Apply applies value to field
func (v *Value) Apply(value reflect.Value)

// ApplyDefault applies default value to field if not already set
func (v *Value) ApplyDefault() error

// Reset resets this value to its default
func (v *Value) Reset() error
```

## Flag Type

Represents a command-line flag.

```go { .api }
// Flag represents a command-line flag
type Flag struct {
    *Value  // Embedded Value

    // Group is the logical grouping when displaying
    Group *Group

    // Xor are mutually exclusive group tags
    Xor []string

    // And are mutually dependent group tags
    And []string

    // PlaceHolder is the placeholder for flag value
    PlaceHolder string

    // Envs are environment variable names
    Envs []string

    // Aliases are flag aliases
    Aliases []string

    // Short is the short flag character
    Short rune

    // Hidden indicates the flag is hidden from help
    Hidden bool

    // Negated is true if the flag was negated
    Negated bool
}
```

### Flag Methods

```go { .api }
// String returns string representation of the flag
func (f *Flag) String() string

// FormatPlaceHolder formats the placeholder string for a Flag
func (f *Flag) FormatPlaceHolder() string
```

## Group Type

Holds metadata about a command or flag group used when printing help.

```go { .api }
// Group holds metadata about a command or flag group used when printing help
type Group struct {
    // Key is the group field tag value used to identify this group
    Key string

    // Title is displayed above the grouped items
    Title string

    // Description is optional, displayed under the Title
    Description string
}
```

## Type Aliases

```go { .api }
// Positional represents a non-branching command-line positional argument
type Positional = *Value

// Command represents a command in the CLI
type Command = *Node

// Argument represents a branching positional argument
type Argument = *Node
```

## Usage Examples

### Working with the Model

```go
package main

import (
    "fmt"
    "github.com/alecthomas/kong"
)

type CLI struct {
    Debug bool `help:"Enable debug mode."`

    Serve struct {
        Port int `help:"Port to listen on." default:"8080"`
    } `cmd:"" help:"Start the server."`

    Version struct{} `cmd:"" help:"Show version."`
}

func main() {
    var cli CLI
    parser := kong.Must(&cli)

    // Access the model
    app := parser.Model

    fmt.Printf("Application name: %s\n", app.Name)
    fmt.Printf("Number of commands: %d\n", len(app.Children))

    // Iterate through commands
    for _, child := range app.Children {
        fmt.Printf("Command: %s\n", child.Name)
        fmt.Printf("  Help: %s\n", child.Help)
        fmt.Printf("  Flags: %d\n", len(child.Flags))
    }

    // Find a specific node
    serveNode := app.Find(&cli.Serve)
    if serveNode != nil {
        fmt.Printf("Found serve command: %s\n", serveNode.Name)
    }
}
```

### Examining Flags

```go
func examineFlags(app *kong.Application) {
    // Get all flags including from ancestors
    allFlags := app.AllFlags(false)

    for depth, flags := range allFlags {
        fmt.Printf("Depth %d flags:\n", depth)
        for _, flag := range flags {
            fmt.Printf("  --%s", flag.Name)
            if flag.Short != 0 {
                fmt.Printf(", -%c", flag.Short)
            }
            fmt.Printf(": %s", flag.Help)
            if flag.HasDefault {
                fmt.Printf(" (default: %s)", flag.Default)
            }
            fmt.Println()
        }
    }
}
```

### Working with Values

```go
func examineValue(val *kong.Value) {
    fmt.Printf("Value: %s\n", val.Name)
    fmt.Printf("  Required: %v\n", val.Required)
    fmt.Printf("  Has default: %v\n", val.HasDefault)

    if val.HasDefault {
        fmt.Printf("  Default: %s\n", val.Default)
    }

    // Check value type characteristics
    if val.IsBool() {
        fmt.Println("  Type: boolean")
    }
    if val.IsSlice() {
        fmt.Println("  Type: slice")
    }
    if val.IsMap() {
        fmt.Println("  Type: map")
    }

    // Check for enum values
    if val.Enum != "" {
        enums := val.EnumSlice()
        fmt.Printf("  Enum values: %v\n", enums)
    }
}
```

### Navigating the Node Tree

```go
func walkNodes(node *kong.Node, depth int) {
    indent := ""
    for i := 0; i < depth; i++ {
        indent += "  "
    }

    fmt.Printf("%s%s (%s)\n", indent, node.Name, node.Type)

    // Visit flags
    for _, flag := range node.Flags {
        fmt.Printf("%s  --%s\n", indent, flag.Name)
    }

    // Visit positionals
    for _, pos := range node.Positional {
        fmt.Printf("%s  <%s>\n", indent, pos.Name)
    }

    // Recursively visit children
    for _, child := range node.Children {
        walkNodes(child, depth+1)
    }
}

func main() {
    var cli CLI
    parser := kong.Must(&cli)

    walkNodes(&parser.Model.Node, 0)
}
```

### Using Groups

```go
type CLI struct {
    // Grouped flags
    Verbose bool `help:"Verbose output." group:"output"`
    Quiet   bool `help:"Quiet output." group:"output"`
    Format  string `help:"Output format." group:"output" enum:"json,yaml,text"`

    Debug   bool `help:"Enable debug." group:"debug"`
    Profile bool `help:"Enable profiling." group:"debug"`
}

func main() {
    var cli CLI
    parser := kong.Must(&cli,
        kong.ExplicitGroups([]kong.Group{
            {Key: "output", Title: "Output Options:", Description: "Control output formatting"},
            {Key: "debug", Title: "Debug Options:", Description: "Development and debugging"},
        }),
    )

    // Groups will be displayed in help text
    ctx, err := parser.Parse(os.Args[1:])
    parser.FatalIfErrorf(err)
}
```

## Visitable Interface

The Visitable interface marks components that can be visited.

```go { .api }
// Visitable is a Visitable component in the model
// This interface contains a private marker method
type Visitable interface {
    // Contains private method - implemented by Application, Node, Flag, Value
}
```

Application, Node, Flag, and Value all implement the Visitable interface, allowing them to be traversed using the `Visit` function (see the Utilities documentation).
