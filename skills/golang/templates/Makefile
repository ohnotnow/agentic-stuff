# Build <name> from a clone and install it:
#
#   make install                       # into ~/.local/bin
#   make install PREFIX=/somewhere     # into /somewhere/bin
#
# The binary is stamped with the git version, the build date, and a mark
# that it was built from source, so `<name> version` can say when a newer
# release is out and `<name> self-update` leaves it alone.
#
# Template from the golang skill: replace NAME, PKG and MAIN below. Taken
# from bothy (github.com/ohnotnow/bothy).

NAME := <name>
# the package holding the Version, Built and FromSource variables
PKG  := github.com/<owner>/<repo>/internal/<name>
# the main package: . when it is the repo root, ./cmd/<name> otherwise
MAIN := .

# ~/.local/bin is the XDG Base Directory spec's folder for a user's own
# programs. /usr/local/bin needs sudo on newer Macs, if it's allowed at all.
PREFIX ?= $(HOME)/.local
BINDIR := $(PREFIX)/bin

VERSION := $(shell git describe --tags --always --dirty 2>/dev/null || echo dev)
BUILT   := $(shell date -u +%Y-%m-%d)
LDFLAGS := -X $(PKG).Version=$(VERSION) -X $(PKG).Built=$(BUILT) -X $(PKG).FromSource=yes

.PHONY: build install

build:
	go build -ldflags "$(LDFLAGS)" -o $(NAME) $(MAIN)

# Copy to a temporary name, then rename over the old binary: macOS kills a
# binary whose file has been overwritten in place.
install: build
	mkdir -p "$(BINDIR)"
	cp $(NAME) "$(BINDIR)/.$(NAME).tmp"
	mv -f "$(BINDIR)/.$(NAME).tmp" "$(BINDIR)/$(NAME)"
	@echo "Installed $(VERSION) to $(BINDIR)/$(NAME)"
	@case ":$$PATH:" in \
		*":$(BINDIR):"*) ;; \
		*) echo; \
		   echo "$(BINDIR) isn't on your PATH. Add this line to ~/.zshrc (or your shell's startup file), then open a new terminal:"; \
		   echo; \
		   echo '  export PATH="$(BINDIR):$$PATH"' ;; \
	esac
