// build.rs - Build script for nanobot-capture-service
// Currently empty - windows crate handles bindgen automatically

fn main() {
    println!("cargo:rerun-if-changed=Cargo.toml");
}
