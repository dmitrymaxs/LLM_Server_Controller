Name:           llmservercontroller
Version:        %{version}
Release:        1%{?dist}
Summary:        Graphical controller for llama.cpp server
License:        MIT
URL:            https://github.com/dmitrymaxs/LLM_Server_Controller

Source0:        LLMServerController-%{version}.tar.gz

BuildArch:      x86_64

%description
LLM Server Controller is a graphical application for configuring
and controlling llama.cpp server.

%prep
%setup -q

%install
mkdir -p %{buildroot}/usr/bin
mkdir -p %{buildroot}/usr/share/applications
mkdir -p %{buildroot}/usr/share/icons/hicolor/16x16/apps
mkdir -p %{buildroot}/usr/share/icons/hicolor/24x24/apps
mkdir -p %{buildroot}/usr/share/icons/hicolor/32x32/apps
mkdir -p %{buildroot}/usr/share/icons/hicolor/48x48/apps
mkdir -p %{buildroot}/usr/share/icons/hicolor/64x64/apps
mkdir -p %{buildroot}/usr/share/icons/hicolor/256x256/apps

install -m 0755 LLMServerController %{buildroot}/usr/bin/LLMServerController
install -m 0644 llmservercontroller.desktop %{buildroot}/usr/share/applications/llmservercontroller.desktop

install -m 0644 16x16.png %{buildroot}/usr/share/icons/hicolor/16x16/apps/llmservercontroller.png
install -m 0644 24x24.png %{buildroot}/usr/share/icons/hicolor/24x24/apps/llmservercontroller.png
install -m 0644 32x32.png %{buildroot}/usr/share/icons/hicolor/32x32/apps/llmservercontroller.png
install -m 0644 48x48.png %{buildroot}/usr/share/icons/hicolor/48x48/apps/llmservercontroller.png
install -m 0644 64x64.png %{buildroot}/usr/share/icons/hicolor/64x64/apps/llmservercontroller.png
install -m 0644 256x256.png %{buildroot}/usr/share/icons/hicolor/256x256/apps/llmservercontroller.png

%files
/usr/bin/LLMServerController
/usr/share/applications/llmservercontroller.desktop
/usr/share/icons/hicolor/16x16/apps/llmservercontroller.png
/usr/share/icons/hicolor/24x24/apps/llmservercontroller.png
/usr/share/icons/hicolor/32x32/apps/llmservercontroller.png
/usr/share/icons/hicolor/48x48/apps/llmservercontroller.png
/usr/share/icons/hicolor/64x64/apps/llmservercontroller.png
/usr/share/icons/hicolor/256x256/apps/llmservercontroller.png