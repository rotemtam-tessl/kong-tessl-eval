package main

import (
	"os/exec"
	"strings"
	"testing"
)

func TestAdd(t *testing.T) {
	cmd := exec.Command("go", "run", ".", "add", "--a=5", "--b=10")
	out, err := cmd.Output()
	if err != nil {
		t.Fatalf("command failed: %v", err)
	}
	got := strings.TrimSpace(string(out))
	if got != "15" {
		t.Errorf("got %q, want %q", got, "15")
	}
}

func TestAddNegative(t *testing.T) {
	// This syntax fails - Kong interprets -2 as a short flag
	cmd := exec.Command("go", "run", ".", "add", "--a", "2", "--b", "-2")
	out, err := cmd.Output()
	if err != nil {
		t.Fatalf("command failed: %v", err)
	}
	got := strings.TrimSpace(string(out))
	if got != "0" {
		t.Errorf("got %q, want %q", got, "0")
	}
}
