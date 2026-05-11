library(shiny)

ui <- fluidPage(
  titlePanel("LABFSG - Teste CI"),
  mainPanel(
    h3("Deploy automatico via merge na main - trigger 7"),
    p("Data UTC:"),
    textOutput("ts")
  )
)

server <- function(input, output, session) {
  output$ts <- renderText(format(Sys.time(), tz = "UTC"))
}

shinyApp(ui, server)
