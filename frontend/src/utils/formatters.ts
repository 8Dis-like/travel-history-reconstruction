export function formatDate(dateString: string): string {
  const date = new Date(dateString)
  return new Intl.DateTimeFormat("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
    timeZone: "UTC"
  }).format(date)
}

export function truncateFilename(filename: string, maxLength: number = 15): string {
  if (filename.length <= maxLength) {
    return filename
  }   

  const lastDotIndex = filename.lastIndexOf(".")
  const extension = filename.slice(lastDotIndex)
  const name = filename.slice(0, lastDotIndex)

  const truncatedName = name.slice(0, maxLength - extension.length - 3)
  return `${truncatedName}...${extension}`
}
