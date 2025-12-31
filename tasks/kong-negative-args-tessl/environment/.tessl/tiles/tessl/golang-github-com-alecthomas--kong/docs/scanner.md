# Scanner and Tokenization

This document covers Kong's scanner, which provides low-level token scanning for command-line arguments. The scanner is used internally by Kong and can also be used directly for custom parsing logic.

## Scanner Type

A stack-based scanner over command-line tokens.

```go { .api }
// Scanner is a stack-based scanner over command-line tokens
type Scanner struct {
    // Internal fields not exported
}
```

## Scanner Creation Functions

```go { .api }
// Scan creates a new Scanner from args with untyped tokens
func Scan(args ...string) *Scanner

// ScanAsType creates a new Scanner from args with the given token type
func ScanAsType(ttype TokenType, args ...string) *Scanner

// ScanFromTokens creates a new Scanner from a slice of tokens
func ScanFromTokens(tokens ...Token) *Scanner
```

## Scanner Methods

### Configuration

```go { .api }
// AllowHyphenPrefixedParameters enables or disables hyphen-prefixed
// flag parameters
func (s *Scanner) AllowHyphenPrefixedParameters(enable bool) *Scanner
```

### Query Methods

```go { .api }
// Len returns the number of input arguments
func (s *Scanner) Len() int

// Peek peeks at the next Token or returns an EOLToken
func (s *Scanner) Peek() Token

// PeekAll returns all remaining tokens
func (s *Scanner) PeekAll() []Token
```

### Consumption Methods

```go { .api }
// Pop pops the front token off the Scanner
func (s *Scanner) Pop() Token

// PopValue pops a value token, or returns an error
func (s *Scanner) PopValue(context string) (Token, error)

// PopValueInto pops a value token into target or returns an error
func (s *Scanner) PopValueInto(context string, target any) error

// PopWhile pops tokens while predicate returns true
func (s *Scanner) PopWhile(predicate func(Token) bool) []Token

// PopUntil pops tokens until predicate returns true
func (s *Scanner) PopUntil(predicate func(Token) bool) []Token
```

### Push Methods

```go { .api }
// Push pushes an untyped Token onto the front
func (s *Scanner) Push(arg any) *Scanner

// PushTyped pushes a typed token onto the front
func (s *Scanner) PushTyped(arg any, typ TokenType) *Scanner

// PushToken pushes a preconstructed Token onto the front
func (s *Scanner) PushToken(token Token) *Scanner
```

## Token Type

Token created by Scanner.

```go { .api }
// Token is a token created by Scanner
type Token struct {
    // Value is the token value
    Value any

    // Type is the token type
    Type TokenType
}
```

### Token Methods

```go { .api }
// String returns string representation
func (t Token) String() string

// IsEOL returns true if this Token is past the end of the line
func (t Token) IsEOL() bool

// InferredType tries to infer the type of a token
func (t Token) InferredType() TokenType

// IsValue returns true if token is usable as a parseable value
func (t Token) IsValue() bool
```

## TokenType

The type of a token.

```go { .api }
// TokenType is the type of a token
type TokenType int

const (
    // UntypedToken is the token type for untyped tokens
    UntypedToken TokenType = 0

    // EOLToken is the token type for end of line
    EOLToken TokenType = 1

    // FlagToken is the token type for long flags (--<flag>)
    FlagToken TokenType = 2

    // FlagValueToken is the token type for flag values (=<value>)
    FlagValueToken TokenType = 3

    // ShortFlagToken is the token type for short flags (-<short>[<tail])
    ShortFlagToken TokenType = 4

    // ShortFlagTailToken is the token type for short flag tail (<tail>)
    ShortFlagTailToken TokenType = 5

    // PositionalArgumentToken is the token type for positional arguments
    PositionalArgumentToken TokenType = 6
)
```

### TokenType Methods

```go { .api }
// String returns string representation of token type
func (t TokenType) String() string

// IsAny returns true if the token's type is any of those provided
func (t TokenType) IsAny(types ...TokenType) bool
```

## Usage Examples

### Basic Scanner Usage

```go
package main

import (
    "fmt"
    "github.com/alecthomas/kong"
)

func main() {
    args := []string{"--verbose", "--port", "8080", "input.txt"}
    scanner := kong.Scan(args...)

    fmt.Printf("Total tokens: %d\n", scanner.Len())

    // Peek at first token without consuming
    token := scanner.Peek()
    fmt.Printf("First token: %v (type: %s)\n", token.Value, token.Type)

    // Pop and process tokens
    for scanner.Len() > 0 {
        token := scanner.Pop()
        fmt.Printf("Token: %v (type: %s)\n", token.Value, token.Type)
    }
}
```

### Consuming Specific Token Types

```go
func parseArgs(args []string) {
    scanner := kong.Scan(args...)

    for scanner.Len() > 0 {
        token := scanner.Pop()

        switch token.Type {
        case kong.FlagToken:
            fmt.Printf("Flag: %v\n", token.Value)

            // Check if next token is a value
            if scanner.Peek().IsValue() {
                value := scanner.Pop()
                fmt.Printf("  Value: %v\n", value.Value)
            }

        case kong.PositionalArgumentToken:
            fmt.Printf("Positional: %v\n", token.Value)

        case kong.EOLToken:
            fmt.Println("End of line")
        }
    }
}
```

### Using PopValue and PopValueInto

```go
func parseCustom(scanner *kong.Scanner) error {
    // Pop a value token with context for error messages
    token, err := scanner.PopValue("port number")
    if err != nil {
        return err
    }

    fmt.Printf("Port token: %v\n", token.Value)

    // Or pop directly into a variable
    var port int
    if err := scanner.PopValueInto("port", &port); err != nil {
        return err
    }

    fmt.Printf("Port value: %d\n", port)
    return nil
}
```

### Using Predicates

```go
func collectFlags(scanner *kong.Scanner) []kong.Token {
    // Pop all flag tokens
    flags := scanner.PopWhile(func(token kong.Token) bool {
        return token.Type == kong.FlagToken
    })

    fmt.Printf("Found %d flags\n", len(flags))
    return flags
}

func collectUntilCommand(scanner *kong.Scanner) []kong.Token {
    // Pop until we hit a positional argument (might be a command)
    tokens := scanner.PopUntil(func(token kong.Token) bool {
        return token.Type == kong.PositionalArgumentToken
    })

    return tokens
}
```

### Creating Scanner with Typed Tokens

```go
func main() {
    // Create scanner with all tokens typed as positional arguments
    scanner := kong.ScanAsType(
        kong.PositionalArgumentToken,
        "file1.txt", "file2.txt", "file3.txt",
    )

    for scanner.Len() > 0 {
        token := scanner.Pop()
        fmt.Printf("%v (type: %s)\n", token.Value, token.Type)
    }
}
```

### Working with Pre-constructed Tokens

```go
func main() {
    tokens := []kong.Token{
        {Value: "--verbose", Type: kong.FlagToken},
        {Value: "true", Type: kong.FlagValueToken},
        {Value: "input.txt", Type: kong.PositionalArgumentToken},
    }

    scanner := kong.ScanFromTokens(tokens...)

    for scanner.Len() > 0 {
        token := scanner.Pop()
        fmt.Printf("%v (type: %s)\n", token.Value, token.Type)
    }
}
```

### Pushing Tokens Back

```go
func parseWithLookahead(scanner *kong.Scanner) {
    // Pop a token
    token := scanner.Pop()

    // Check if we want to process it
    if shouldSkip(token) {
        // Push it back for later processing
        scanner.PushToken(token)
        return
    }

    // Or push a different token
    scanner.Push("replacement-value")

    // Or push with specific type
    scanner.PushTyped("--flag", kong.FlagToken)
}

func shouldSkip(token kong.Token) bool {
    // Custom logic
    return false
}
```

### Token Type Inference

```go
func examineToken(token kong.Token) {
    // Check actual type
    fmt.Printf("Token type: %s\n", token.Type)

    // Try to infer type if untyped
    if token.Type == kong.UntypedToken {
        inferred := token.InferredType()
        fmt.Printf("Inferred type: %s\n", inferred)
    }

    // Check if usable as a value
    if token.IsValue() {
        fmt.Println("Can be used as a value")
    }

    // Check if end of line
    if token.IsEOL() {
        fmt.Println("End of line reached")
    }
}
```

### Checking Multiple Token Types

```go
func processToken(token kong.Token) {
    if token.Type.IsAny(kong.FlagToken, kong.ShortFlagToken) {
        fmt.Println("This is some kind of flag")
    }

    if token.Type.IsAny(
        kong.PositionalArgumentToken,
        kong.FlagValueToken,
        kong.UntypedToken,
    ) {
        fmt.Println("This can be used as a value")
    }
}
```

### Custom Mapper Using Scanner

```go
type Pair struct {
    Key   string
    Value string
}

func (p *Pair) Decode(ctx *kong.DecodeContext) error {
    // Pop the key=value string
    var s string
    if err := ctx.Scan.PopValueInto("key=value", &s); err != nil {
        return err
    }

    // Split into key and value
    parts := strings.SplitN(s, "=", 2)
    if len(parts) != 2 {
        return fmt.Errorf("expected key=value format")
    }

    p.Key = parts[0]
    p.Value = parts[1]
    return nil
}

type CLI struct {
    Pair Pair `help:"Key-value pair."`
}
```

### Advanced Scanner with Peeking

```go
func parseComplexFormat(scanner *kong.Scanner) error {
    // Peek to see what's coming
    next := scanner.Peek()

    if next.Type == kong.FlagToken {
        // It's a flag, check if it has a value
        flag := scanner.Pop()

        peek := scanner.Peek()
        if peek.IsValue() {
            value := scanner.Pop()
            fmt.Printf("Flag %v = %v\n", flag.Value, value.Value)
        } else {
            fmt.Printf("Boolean flag %v\n", flag.Value)
        }
    }

    return nil
}
```

### Getting All Remaining Tokens

```go
func captureRemaining(scanner *kong.Scanner) []kong.Token {
    // Get all remaining tokens without consuming
    tokens := scanner.PeekAll()

    fmt.Printf("Remaining tokens: %d\n", len(tokens))

    for _, token := range tokens {
        fmt.Printf("  %v (type: %s)\n", token.Value, token.Type)
    }

    return tokens
}
```

### Hyphen-Prefixed Parameters

```go
func main() {
    scanner := kong.Scan("--negative-number", "-42")

    // By default, -42 would be interpreted as a flag
    token := scanner.Pop() // --negative-number
    next := scanner.Pop()  // Would be FlagToken for -42

    // Enable hyphen-prefixed parameters
    scanner2 := kong.Scan("--negative-number", "-42")
    scanner2.AllowHyphenPrefixedParameters(true)

    scanner2.Pop() // --negative-number
    next2 := scanner2.Pop() // Now -42 is a value, not a flag
    fmt.Printf("Value: %v\n", next2.Value)
}
```

### Building a Custom Parser

```go
type CustomParser struct {
    scanner *kong.Scanner
}

func NewCustomParser(args []string) *CustomParser {
    return &CustomParser{
        scanner: kong.Scan(args...),
    }
}

func (p *CustomParser) ParseCommand() (string, []string, error) {
    // First token should be the command
    if p.scanner.Len() == 0 {
        return "", nil, fmt.Errorf("no command provided")
    }

    cmdToken, err := p.scanner.PopValue("command")
    if err != nil {
        return "", nil, err
    }

    command := fmt.Sprint(cmdToken.Value)

    // Collect remaining arguments
    var args []string
    for p.scanner.Len() > 0 {
        token := p.scanner.Pop()
        if !token.IsEOL() {
            args = append(args, fmt.Sprint(token.Value))
        }
    }

    return command, args, nil
}
```
