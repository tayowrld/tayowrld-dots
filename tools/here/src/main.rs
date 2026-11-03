// HERE - directory information highlighter
// here [-f | --full] - show information about current directory
// here [-f | --full] [path/to/dir] - show information about directory `dir`

use std::{env,io,fs,path::PathBuf, path::Path, error::Error};
use clap::Parser;

#[derive(Parser)]
#[command(version,about)]


struct Cli {
    path: Option<String>,
    #[arg(short,long, default_value_t=false)]
    full: bool
}


fn get_current_directory_path() -> io::Result<PathBuf> {
    env::current_dir()
}

fn here_exists_on_path(path: &PathBuf, keep_path: &mut PathBuf) -> bool {
    let paths = fs::read_dir(path).unwrap();
    let mut is_here_in = false;
    for path in paths {
        if path.as_ref().unwrap().file_name().display().to_string() == String::from(".here") {
            is_here_in = true;
            *keep_path = path.unwrap().path();
        }    
    }
    is_here_in
}

fn read_here_to_string(path: &PathBuf) -> Option<String>{
    fs::read_to_string(path).ok()
}


fn main() -> Result<(), Box<dyn Error>>{
    let cli = Cli::parse();

    let mut here_path: PathBuf = Default::default();
    //let _ = debug();
    let is_full: bool = cli.full;
    let bind_path = match cli.path {
        Some(bind_path) => bind_path,
        None => get_current_directory_path()?.display().to_string(),
    };
    let cli_path = Path::new(&bind_path);
    let is_path_ok = fs::exists(cli_path);
    

    let mut here_exists:bool;
    if is_path_ok? {
        here_exists = here_exists_on_path(
            &PathBuf::from(cli_path), 
            &mut here_path
        );
    } else {
        here_exists = here_exists_on_path(
            &get_current_directory_path()?, 
            &mut here_path
        );
    }

    print!("\x1b[33m");
    if !here_exists {
        println!("");
    } else{
        let contents = read_here_to_string(&here_path).ok_or("")?;
        if !is_full {
            let content_lines: Vec<&str> = contents.split('\n').collect();
            println!("{}",content_lines[0]);
        } else {
            println!("{}",contents);
        }
    }
    print!("\x1b[0m");
    Ok(())
}
