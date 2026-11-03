vim.opt.number = true
vim.opt.relativenumber = true
vim.opt.signcolumn = "yes"
vim.opt.tabstop = 2
vim.opt.softtabstop = 2
vim.opt.shiftwidth = 2

vim.lsp.config("rust_analyzer", {
    cmd = { "rust-analyzer" },
    filetypes = { "rust" },
    root_markers = { "Cargo.toml", "rust-project.json" },

    settings = {
        ["rust-analyzer"] = {
            check = {
                command = "clippy",
            },
        },
    },
})

vim.lsp.enable("rust_analyzer")

vim.api.nvim_create_autocmd("LspAttach", {
    callback = function(args)
        vim.lsp.completion.enable(
            true,
            args.data.client_id,
            args.buf,
            { autotrigger = true }
        )
    end,
})

vim.opt.completeopt = { "menuone", "noselect", "popup" }

vim.diagnostic.config({
    virtual_text = true,
    underline = true,
    signs = true,
})

vim.keymap.set("n", "gd", vim.lsp.buf.definition)
vim.keymap.set("n", "gr", vim.lsp.buf.references)
vim.keymap.set("n", "K", vim.lsp.buf.hover)
vim.keymap.set("n", "<leader>rn", vim.lsp.buf.rename)
vim.keymap.set("n", "<leader>ca", vim.lsp.buf.code_action)

vim.keymap.set("n", "[d", function()
    vim.diagnostic.jump({ count = -1 })
end)

vim.keymap.set("n", "]d", function()
    vim.diagnostic.jump({ count = 1 })
end)
