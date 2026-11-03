use clap::{Parser,Subcommand}; 

#[derive(Parser)]
pub(crate) struct Cli{
    #[command(subcommand)]
    pub(crate) action: Action,
    #[arg(long,short)]
    pub(crate) date: Option<String>,
}

#[derive(Subcommand)]
pub(crate) enum Action{
    List,
    Add {
        title: String,
    },
    Done {
        index: usize,
    },
    Remove {
        index: usize,
    },
}

