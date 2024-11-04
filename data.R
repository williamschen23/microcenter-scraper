library(tidyverse)
dat <- read.csv('data.csv')

plotItem <- function(data, name){
  tempdat <- data %>% filter(Name == name)
  tempdat$Time = as.Date(tempdat$Time, "%Y-%m-%d")
  tempdat_clean <- na.omit(tempdat)
  print(ggplot(data=tempdat_clean, aes(x=Time, y=Discounted_Price)) +
          geom_point() + 
          theme_classic() + 
          ggtitle(name))
}

str(dat)

# plotItem(dat,"AMD Ryzen™ 7 7700X, Gigabyte B650 Gaming X AX v2, 32GB DDR5")

for(item in unique(dat$Name)){
  plotItem(dat, item)
}
